from langchain_community.document_loaders import GoogleDriveLoader
from langchain_community.document_loaders import UnstructuredFileIOLoader
from dotenv import load_dotenv

load_dotenv()

loader = GoogleDriveLoader(
    file_ids=["18gH6Enj5pE7cQYJZNAgr8eRNskFOWzlb"],
    file_loader_cls=UnstructuredFileIOLoader,
)

data = loader.load()
