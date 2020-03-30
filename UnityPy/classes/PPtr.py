from ..streams import EndianBinaryReader, EndianBinaryWriter


class PPtr:
    def __init__(self, reader: EndianBinaryReader):
        self.index = -2
        self.file_id = reader.read_int()
        self.path_id = reader.read_int() if reader.version2 < 14 else reader.read_long()
        self.assets_file = reader.assets_file

    def __getattr__(self, key):
        # get manager
        manager = None
        if self.file_id == 0:
            manager = self.assets_file

        elif self.file_id > 0 and self.file_id - 1 < len(self.assets_file.externals):
            if self.index == -2:
                external_name = self.assets_file.externals[self.file_id - 1].name

                files = self.assets_file.parent.files
                if external_name not in files:
                    external_name = external_name.upper()
                manager = self.assets_file.parent.files[external_name]

        if manager and self.path_id in manager.objects:
            self = manager.objects[self.path_id]
            return getattr(self, key)

        raise NotImplementedError("PPtr")

        """
				if (!assetsFileIndexCache.TryGetValue(name, out index))
				{
					index = assetsFileList.FindIndex(x => x.upperFileName == name);
					assetsFileIndexCache.Add(name, index);
				}
			}

			if (index >= 0)
			{
				result = assetsFileList[index];
				return true;
			}
		}
		if self.path_id in self.assets_file.objects:
			return self.assets_file.objects[self.path_id]
		else:
			return super(PPtr, self).__new__(self)
	"""

    def __repr__(self):
        return self.__class__.__name__

    def __bool__(self):
        return False


def save_ptr(obj, writer: EndianBinaryWriter):
    if isinstance(obj, PPtr):
        writer.write_int(obj.file_id)
        writer.write_int(obj.path_id)
    else:
        writer.write_int(0)  # it's usually 0......
        writer.write_int(obj.path_id)


"""	
	def TryGetAssetsFile(self):
		result = None
		if m_FileID == 0:
			return self.assets_file

		if m_FileID > 0 and m_FileID - 1 < len(self.assets_file.externals):
			var assetsManager = assetsFile.assetsManager
			var assetsFileList = assetsManager.assetsFileList
			var assetsFileIndexCache = assetsManager.assetsFileIndexCache

			if self.index == -2:
				external_name = self.assets_file.eternals[self.file_id - 1].filename

				
				if (!assetsFileIndexCache.TryGetValue(name, out index))
				{
					index = assetsFileList.FindIndex(x => x.upperFileName == name);
					assetsFileIndexCache.Add(name, index);
				}
			}

			if (index >= 0)
			{
				result = assetsFileList[index];
				return true;
			}
		}

		return false;
	}

		public bool TryGet(out T result)
		{
			if (TryGetAssetsFile(out var sourceFile))
			{
				if (sourceFile.Objects.TryGetValue(m_PathID, out var obj))
				{
					if (obj is T variable)
					{
						result = variable;
						return true;
					}
				}
			}

			result = null;
			return false;
		}

		public bool TryGet<T2>(out T2 result) where T2 : Object
		{
			if (TryGetAssetsFile(out var sourceFile))
			{
				if (sourceFile.Objects.TryGetValue(m_PathID, out var obj))
				{
					if (obj is T2 variable)
					{
						result = variable;
						return true;
					}
				}
			}

			result = null;
			return false;
		}

		public void Set(T m_Object)
		{
			var name = m_Object.assetsFile.upperFileName;
			if (string.Equals(assetsFile.upperFileName, name, StringComparison.Ordinal))
			{
				m_FileID = 0;
			}
			else
			{
				m_FileID = assetsFile.m_Externals.FindIndex(x => string.Equals(x.fileName, name, StringComparison.OrdinalIgnoreCase));
				if (m_FileID == -1)
				{
					assetsFile.m_Externals.Add(new FileIdentifier
					{
						fileName = m_Object.assetsFile.fileName
					});
					m_FileID = assetsFile.m_Externals.Count;
				}
				else
				{
					m_FileID += 1;
				}
			}

			var assetsManager = assetsFile.assetsManager;
			var assetsFileList = assetsManager.assetsFileList;
			var assetsFileIndexCache = assetsManager.assetsFileIndexCache;

			if (!assetsFileIndexCache.TryGetValue(name, out index))
			{
				index = assetsFileList.FindIndex(x => x.upperFileName == name);
				assetsFileIndexCache.Add(name, index);
			}

			m_PathID = m_Object.m_PathID;
		}

		public bool IsNull => m_PathID == 0 || m_FileID < 0;
	}
}
"""
