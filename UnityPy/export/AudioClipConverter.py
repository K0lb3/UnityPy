from ..enums import AudioType, AudioCompressionFormat, AUDIO_TYPE_EXTEMSION

try:
	from fsb5 import FSB5
except ImportError:
	print('Couldn\'t import fsb5.\nfsb5 is required to process convert audio clips.')

def extract_audioclip_samples(d) -> dict:
	"""
    Copied from unitypack - https://github.com/HearthSim/UnityPack/blob/d9ce99fac3c917fa44b0042c9114b7cd03aa9884/unitypack/utils.py#L14
    
	Extract all the sample data from an AudioClip and
	convert it from FSB5 if needed.
	"""
	ret = {}

	if not d.m_AudioData:
		# eg. StreamedResource not available
		return {}

	af = FSB5(d.m_AudioData)
	for i, sample in enumerate(af.samples):
		if i > 0:
			filename = "%s-%i.%s" % (d.name, i, af.get_sample_extension())
		else:
			filename = "%s.%s" % (d.name, af.get_sample_extension())
		try:
			sample = af.rebuild_sample(sample)
		except ValueError as e:
			print("WARNING: Could not extract %r (%s)" % (d, e))
			continue
		ret[filename] = sample

	return ret