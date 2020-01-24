class PPtr:
	def __init__(self, reader):
		# super().__init__(reader = reader)
		pass

	def __new__(cls, reader):
		cls.file_id = reader.read_int()
		cls.path_id = reader.read_int() if reader.version2 < 14 else reader.read_long()
		cls.assets_file = reader.assets_file
		if cls.path_id in cls.assets_file.objects:
			return cls.assets_file.objects[cls.path_id]
		else:
			return super(PPtr, cls).__new__(cls)

	def __getattr__(self, item):
		return None

	def __repr__(self):
		return "<%s %s>" % (
			self.__class__.__name__
		)

	def __bool__(self):
		return False


"""
	def TryGetAssetsFile(self):
		result = None
		if self.file_id == 0:
			return self.assets_file

		if self.file_id > 0 and self.file_id - 1 < len(self.assets_file._externals):
			assets_manager = self.assets_file.assets_manager
			assets = assets_manager.assets

			if self.index == -2:
				external = assets_file._externals[self.file_id - 1]
				name = external.file_name

				var assetsManager = assetsFile.assetsManager;
				var assetsFileList = assetsManager.assetsFileList;
				var assetsFileIndexCache = assetsManager.assetsFileIndexCache;

				if index == -2: #
						var m_External = assetsFile.m_Externals[m_FileID - 1];
					var name = m_External.fileName.ToUpper();
					if !assetsFileIndexCache.TryGetValue(name, out index): #
							index = assetsFileList.FindIndex(x => x.upperFileName == name);
						assetsFileIndexCache.Add(name, index);
					if self.index >= 0:
				return assets[self.index]

		 return False

		public bool TryGet(out T result)
				if TryGetAssetsFile(out var sourceFile): #
					if sourceFile.Objects.TryGetValue(m_PathID, out var obj): #
						if obj is T variable: #
							result = variable;
						return true;

			result = null;
			return false;

		public bool TryGet<T2>(out T2 result) where T2 : Object
				if TryGetAssetsFile(out var sourceFile): #
					if sourceFile.Objects.TryGetValue(m_PathID, out var obj): #
						if obj is T2 variable: #
							result = variable;
						return true;

			result = null;
			return false;

		public void Set(T m_Object)
				var name = m_Object.assetsFile.upperFileName;
			if string.Equals(assetsFile.upperFileName, name, StringComparison.Ordinal): #
					m_FileID = 0;
				else
					m_FileID = assetsFile.m_Externals.FindIndex(x => string.Equals(x.fileName, name, StringComparison.OrdinalIgnoreCase));
				if m_FileID == -1: #
						assetsFile.m_Externals.Add(new FileIdentifier
							fileName = m_Object.assetsFile.fileName
					});
					m_FileID = assetsFile.m_Externals.Count;
					else
						m_FileID += 1;

			var assetsManager = assetsFile.assetsManager;
			var assetsFileList = assetsManager.assetsFileList;
			var assetsFileIndexCache = assetsManager.assetsFileIndexCache;

			if !assetsFileIndexCache.TryGetValue(name, out index): #
					index = assetsFileList.FindIndex(x => x.upperFileName == name);
				assetsFileIndexCache.Add(name, index);

			m_PathID = m_Object.m_PathID;

		public bool IsNull() => m_PathID == 0 or m_FileID < 0;
		"""
