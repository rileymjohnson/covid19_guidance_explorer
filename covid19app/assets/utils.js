const parsePatternMatchingId = id => {
	const separatorIndex = id.lastIndexOf('.')
	const property = id.slice(separatorIndex)
	const patternMatchingId = JSON.parse(
		id.slice(0, separatorIndex)
	)
	return {
		id: patternMatchingId,
		property
	}
}
