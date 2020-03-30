import os

from .helpers import ImportHelper


class ResourceReader:
    need_search: bool
    path: str
    assets_file: None
    offset: int
    size: int

    def __init__(self, *args):
        """
		Input:
		Option 1:
			path - file path
			assets_file - SerializedFile
			offset -
			size -
		Option 2:
			reader - EndianBinaryReader
			offset -
			size -
		"""
        if len(args) == 4:
            self.need_search = True
            self.path = args[0]
            self.assets_file = args[1]
        elif len(args) == 3:
            self.need_search = False
            self.reader = args[0]
        self.offset = args[-2]
        self.size = args[-1]

    def get_data(self):
        if self.need_search:
            resource_file_name = os.path.basename(self.path)

            reader = self.assets_file.assets_manager.resource_file_readers.get(
                resource_file_name
            )
            if reader:
                reader.Position = self.offset
                return reader.read_bytes(self.size)

            current_directory = os.path.dirname(self.assets_file.full_name)
            resource_file_path = os.path.join(current_directory, resource_file_name)
            if not os.path.isfile(resource_file_path):
                find_files = ImportHelper.find_all_files(
                    current_directory, resource_file_name
                )
                if find_files:
                    resource_file_path = find_files[0]

            if os.path.isfile(resource_file_path):
                with open(resource_file_path, "rb") as f:
                    f.seek(self.offset)
                    return f.read(self.size)
            else:
                raise FileNotFoundError(
                    f"Can't find the resource file {resource_file_name}"
                )

        else:
            self.reader.Position = self.offset
            return self.reader.read_bytes(self.size)
