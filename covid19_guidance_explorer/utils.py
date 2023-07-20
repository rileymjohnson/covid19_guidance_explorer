from typing import Union, List, Iterable, Tuple, TypeVar, Optional
from selectolax.parser import HTMLParser, Node
from playhouse.postgres_ext import Model
from uuid import uuid5, NAMESPACE_URL
from mimetypes import guess_type
from numbers import Number
from peewee import Field
from pathlib import Path

from furl import furl
import hashlib
import random
import base64
import fitz
import re

from PyQt6.QtGui import (
    QPageLayout,
    QPageSize,
    QColor,
    QImageReader,
    QPageRanges,
    QImage,
)
from PyQt6.QtCore import QMarginsF, QByteArray, QBuffer, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication

from covid19_guidance_explorer.config import config


COLORS = QColor.colorNames()


def random_color() -> str:
    return random.choice(COLORS)


class PeeweeHelpers:
    @staticmethod
    def all_but(
        model: Model,
        fields: Union[Field, List[Field]]
    ) -> List[Field]:
        if isinstance(fields, Field):
            fields = [fields]
        fields = [f.name for f in fields]

        all_but_fields = []

        for field_name in model._meta.sorted_field_names:
            if field_name not in fields:
                all_but_fields.append(getattr(model, field_name))

        return all_but_fields


def base64_encode_file(file: str | Path) -> str:
    mimetype, _ = guess_type(str(file))

    with open(file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
        data = f"data:{mimetype};base64,{data}"

    return data


def load_file(file: str) -> str:
    try:
        return Path(file).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(file).read_text()


def file_to_url(file: str | Path) -> str:
    if isinstance(file, str):
        file = Path(file)

    assets_base = Path(config["paths"]["assets_folder"]).parent

    url = file.relative_to(assets_base).as_posix()

    return f"/{url}"


supplementary_file_formats = [
    ".css",
    ".png",
    ".jpeg",
    ".jpg",
    ".svg",
    ".gig",
    ".tif",
    ".tiff",
    ".ico",
    ".webp",
    ".mp3",
    ".wav",
    ".ogg",
    ".mp4",
    ".webm",
]


def clean_url(original_url, root_url):
    search = re.search(
        "^(?:https://web.archive.org)?/web/[0-9]{14}[^/]*/(.*)$", original_url
    )

    if search:
        fixed_url = furl(search.groups()[0])
    else:
        fixed_url = furl(original_url)

    fixed_url = fixed_url.remove(fragment=True, args=True)

    if fixed_url.url.startswith("//"):
        return fixed_url.set(scheme="https").url
    elif fixed_url.url.startswith("/"):
        return furl(root_url).set(path="").add(path=fixed_url.url).url
    else:
        return fixed_url.url


def get_url_suffix(url: str) -> str:
    path = furl(url).remove(fragment=True, args=True).pathstr

    return Path(path).suffix.lower()


def asset_file_to_url(asset_file: Path) -> str:
    asset_url = asset_file.relative_to(
        config["paths"]["project_root"]
    ).as_posix()

    return f"/{asset_url}"


def is_data_url(url: str) -> bool:
    return url.strip().lower().startswith("data:")


def is_anchor_url(url: str) -> bool:
    return url.startswith("#")


def resolve_url(url: str, base_url: str) -> str:
    base_url = furl(base_url).remove(fragment=True, args=True)

    base_url \
        .set(path=base_url.path.segments[:-1]) \
        .add(path=url) \
        .path \
        .normalize()

    return base_url.url


def remove_outside_quotes(string):
    return re.sub("""(?:^['"])|(?:['"]$)""", "", string)


css_asset_urls_regex = re.compile(r"""(?<=url\()[^)]+(?=\))""", re.IGNORECASE)


def extract_asset_urls_from_css(
    css: str, base_url: str
) -> Iterable[Tuple[str, str]]:
    for original_url in css_asset_urls_regex.findall(css):
        original_url = remove_outside_quotes(original_url)

        if not is_data_url(original_url) and not is_anchor_url(original_url):
            url = furl(original_url).remove(fragment=True, args=True)

            if url.netloc is not None:
                yield original_url, url.url
            elif url.url.startswith("/"):
                yield original_url, furl(base_url).set(path=url.path).url
            else:
                yield original_url, resolve_url(url.url, base_url)


css_asset_imports_regex = re.compile(
    r"""@import +(?:url\()?['"]?([^.]+\.css)[^;]+;""", re.IGNORECASE
)


def extract_import_urls_from_css(
    css: str, base_url: str
) -> Iterable[Tuple[str, str]]:
    for match in css_asset_imports_regex.finditer(css):
        import_statement = match.group()

        for import_file in match.groups():
            import_url = resolve_url(import_file, base_url)
            yield import_statement, import_url


def resolve_css_urls(css: str, root_url: str) -> str:
    extracted_urls = extract_asset_urls_from_css(css, root_url)
    extractions_to_replace = []

    for original_url, extracted_url in extracted_urls:
        extracted_url = clean_url(extracted_url, root_url)
        extracted_url_file = get_asset_url_file_identifier(extracted_url)
        extracted_url_asset_path = asset_file_to_url(extracted_url_file)

        extractions_to_replace.append((original_url, extracted_url_asset_path))

    extractions_to_replace = sorted(
        extractions_to_replace,
        key=lambda i: -len(i[0])
    )

    for old_url, new_url in extractions_to_replace:
        css = css.replace(old_url, new_url)

    return css


def resolve_css_imports(css: str, base_url: str) -> str:
    imports = extract_import_urls_from_css(css, base_url)

    for import_statement, import_url in imports:
        import_file = get_asset_url_file_identifier(import_url)
        import_css = load_file(import_file)

        css = css.replace(import_statement, import_css)

    return css


def resolve_css(css: str, base_url: str) -> str:
    css = resolve_css_imports(css, base_url)
    css = resolve_css_urls(css, base_url)

    return css


def replace_css_entity(tag: Node, css: str) -> None:
    if tag.tag in ("style", "link"):
        style_tag = HTMLParser(f"<style>{css}</style>").head.child

        if tag.tag == "style":
            for attr, val in tag.attrs.items():
                style_tag.attrs[attr] = val

        tag.replace_with(style_tag)
    else:
        tag.attrs["style"] = css


def get_asset_url_file_identifier(url: str) -> Path:
    root_url = furl(url).remove(fragment=True, path=True, args=True)

    folder_name = uuid5(NAMESPACE_URL, root_url.url)

    folder = Path(
        config["paths"]["supplementary_files_dir"]
    ).joinpath(str(folder_name))

    if not folder.exists():
        folder.mkdir()

    identifier = uuid5(NAMESPACE_URL, url)

    suffix = get_url_suffix(url)

    return folder.joinpath(str(identifier)).with_suffix(suffix)


def get_asset_tags(html: HTMLParser) -> Iterable[Tuple[Node, str, str]]:
    for css_query, attr in [
        (r"svg image[xlink\:href]", "xlink:href"),
        (
            "*:matches(source, track, audio, video, embed, iframe, img)[src]",
            "src"
        ),
        ("object[data]", "data"),
        ('link[rel*="stylesheet"][href]', "href"),
    ]:
        for tag in html.css(css_query):
            url = tag.attrs.get(attr)

            if url is not None:
                if get_url_suffix(url) in supplementary_file_formats:
                    yield tag, url, attr


def load_html_document(document: TypeVar("DocumentVersion")) -> str:
    if document.file_type.mimetype != "text/html":
        raise ValueError("This method can only be used on HTML documents.")

    root_url = getattr(document, "source", None)
    file = getattr(document, "file", None)

    if root_url is None:
        raise ValueError(
            "This document does not have a source attached to it. "
            "In order to resolve and load relative paths, a "
            "document source is needed."
        )

    if file is None:
        raise ValueError("This document does not have a file attached to it.")

    html = load_file(file)
    html = HTMLParser(html)

    for script_tag in html.css("script"):
        script_tag.decompose()

    for tag in html.css("style, *[style]"):
        if tag.tag == "style":
            css = tag.text(strip=True)
        else:
            css = tag.attrs.get("style", "")

        css = resolve_css(css, root_url)

        replace_css_entity(tag, css)

    for tag, url, attr in get_asset_tags(html):
        url = clean_url(url, root_url)
        asset_file = get_asset_url_file_identifier(url)

        if tag.tag == "link":
            css = load_file(asset_file)

            base_url = clean_url(tag.attrs.get("href"), root_url)

            css = resolve_css(css, base_url)

            replace_css_entity(tag, css)
        else:
            tag.attrs[attr] = asset_file_to_url(asset_file)

    for tag in html.css("html, body"):
        tag_style = tag.attrs.get("style", "")
        tag.attrs["style"] = f"min-width: unset;{tag_style}"

    return html.html


def generate_html_thumbnail(document: TypeVar("DocumentVersion")) -> QImage:
    html = load_html_document(document)

    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    image = None

    def _print_finished_callback(pdf_bytes: QByteArray) -> None:
        pdf_buffer = QBuffer(pdf_bytes)
        image_reader = QImageReader(pdf_buffer)

        nonlocal image
        image = image_reader.read()

        app.quit()

    layout = QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Portrait,
        QMarginsF(0, 0, 0, 0),
    )

    page_range = QPageRanges()
    page_range.addPage(1)

    loader = QWebEngineView()
    loader.setZoomFactor(1)
    loader.setHtml(html)

    loader.loadFinished.connect(
        lambda _: loader.printToPdf(
            _print_finished_callback,
            layout,
            page_range
        )
    )

    app.exec()

    return image


def generate_pdf_thumbnail(document: TypeVar("DocumentVersion")) -> QImage:
    try:
        with fitz.open(document.file) as pdf:
            if pdf.page_count == 0:
                raise fitz.EmptyFileError()

            first_page = pdf.load_page(0)

            image_bytes = first_page.get_pixmap().tobytes()

            return QImage.fromData(image_bytes)

    except (fitz.FileDataError, fitz.FileNotFoundError, fitz.EmptyFileError):
        ...


def generate_document_thumbnail(
    document: TypeVar("DocumentVersion"),
    save_file: Optional[Path | str] = None,
    size: Tuple[int, int] = (256, 256),
) -> None:
    if save_file is None:
        save_file = document.thumbnail_file
    elif isinstance(save_file, Path):
        save_file = save_file.as_posix()

    image = None

    if document.file_type.mimetype == "application/pdf":
        image = generate_pdf_thumbnail(document)

    if document.file_type.mimetype == "text/html":
        image = generate_html_thumbnail(document)

    if image is None:
        image = QImage(config["paths"]["no_thumbnail_file"])

    image = image.scaled(
        *size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

    image.save(save_file)


def insert_text_into_pdf_page(
    page: fitz.Page,
    text: str,
    *,
    horizontal_align_text: Optional[str] = "left",
    vertical_align_text: Optional[str] = "top",
    horizontal_offset: Number = 25,
    vertical_offset: Number = 15,
    font_name: str = "helv",
    font_size: int = 11,
    color: Tuple[int, int, int] = (0, 0, 0),
) -> None:
    page.clean_contents()

    text_width = fitz.get_text_length(
        text=text,
        fontname=font_name,
        fontsize=font_size
    )

    if vertical_align_text == "top":
        vertical_point = vertical_offset
    elif vertical_align_text == "bottom":
        vertical_point = page.mediabox[3] - vertical_offset
    else:
        raise ValueError(
            "Invalid vertical_align_text argument"
        )

    if horizontal_align_text == "left":
        text_point = fitz.Point(horizontal_offset, vertical_point)
    elif horizontal_align_text == "center":
        text_point = fitz.Point((
            page.mediabox[2] - text_width) / 2,
            vertical_point
        )
    elif horizontal_align_text == "right":
        text_point = fitz.Point(
            page.mediabox[2] - text_width - horizontal_offset, vertical_point
        )
    else:
        raise ValueError(
            "Invalid horizontal_align_text argument"
        )

    page.insert_text(
        point=text_point,
        text=text,
        fontname=font_name,
        fontsize=font_size,
        color=color,
        rotate=0,
    )


def remove_trailing_whitespace(tag: Node) -> None:
    child_tag = tag.last_child

    if child_tag is None:
        return

    while (child_tag := child_tag.prev) is not None:
        if child_tag.text(strip=True) == "":
            child_tag.decompose()
        else:
            break


def remove_leading_whitespace(tag: Node) -> None:
    child_tag = tag.child

    if child_tag is None:
        return

    while (child_tag := child_tag.next) is not None:
        if child_tag.prev.text(strip=True) == "":
            child_tag.prev.decompose()
        else:
            break


def remove_extraneous_tags(tag: Node) -> None:
    tags_to_unwrap = tag.css("*:not(mark):not(span.headline-wrapper)")

    for child_tag in tags_to_unwrap:
        if child_tag.text(strip=True) == "":
            child_tag.replace_with(" ")
        else:
            child_tag.unwrap()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_headline(headline: str) -> str:
    headline = HTMLParser(
        f'<span class="headline-wrapper">{headline}</span>'
    ).body.child

    remove_leading_whitespace(headline)
    remove_trailing_whitespace(headline)
    remove_extraneous_tags(headline)

    html = normalize_whitespace(headline.html)

    return html


def insert_html_as_pdf(
    pdf: fitz.Document,
    html: str | HTMLParser,
    *,
    page_margins: Tuple[Number, Number, Number, Number] = (25, 25, 25, 25),
    start_index: int = -1,
) -> None:
    if isinstance(html, HTMLParser):
        html = html.html

    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    def _print_finished_callback(save_bytes: QByteArray) -> None:
        with fitz.open(stream=save_bytes.data()) as temp_pdf:
            pdf.insert_pdf(temp_pdf, start_at=start_index)

        app.quit()

    layout = QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Portrait,
        QMarginsF(*page_margins),
    )

    loader = QWebEngineView()
    loader.setZoomFactor(1)
    loader.setHtml(html)

    loader.loadFinished.connect(
        lambda _: loader.page().printToPdf(_print_finished_callback, layout)
    )

    app.exec()


def hash_file(file: str | Path) -> str:
    sha256 = hashlib.sha256()

    file_mem_view = memoryview(bytearray(128 * 1024))

    with open(file, "rb", buffering=0) as f:
        while n := f.readinto(file_mem_view):
            sha256.update(file_mem_view[:n])

    return sha256.hexdigest()


def hash_text(text: str | bytes) -> str:
    if isinstance(text, str):
        text = text.encode()

    return hashlib.sha256(text).hexdigest()
