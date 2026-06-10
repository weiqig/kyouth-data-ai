import os
from pathlib import Path
from email import policy
from email.parser import BytesParser


class Ingestor:
    '''
    Ingestor class used to perform data ingestion.
    Extracts and decodes job listings from provided
    seed 0_source/*.mhtml files into raw 1_bronze/*.html format.
    '''
    def __init__(self, input_dir: str, output_dir: str):
        '''
        Initialize the ingestor class variables.
        '''
        self.extracted = 0
        self.failed = 0
        self.total = 0
        self.src_dir = Path(input_dir)
        self.out_dir = Path(output_dir)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def ingest_all_mhtml(self):
        '''
        Execute the ingestion process.
        '''
        print("week1 [week1] python main.py ingest")
        print("🥉 Bronze:...")

        if not self.src_dir.exists():
            pass
        else:
            for path in self.src_dir.glob("*.mhtml"):
                filename = path.stem
                content = self.extract_html_from_mhtml(filename)

                if content:
                    destination = self.out_dir / f"{filename}.html"
                    if destination.exists():
                        print(f"{filename}.html already exists, proceeding...")
                    else:
                        destination.write_text(content, encoding="utf-8")
                        self.extracted += 1
                        print(f"✅ Extracted: {filename}.mhtml")
                else:
                    self.failed += 1
                    print(f"⚠️ No HTML content found in: {filename}.mhtml")

                self.total += 1

        print("")
        self.get_results()

    def extract_html_from_mhtml(self, filename: str) -> str | None:
        '''
        Extracts html content from mhtml file if able.

        Arguments:
            filename: str - the file to be processed.
            ...
        '''
        path = Path(f"{self.src_dir}/{filename}.mhtml")
        if not path.exists():
            return None

        msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())

        for part in msg.walk():
            if part.get_content_type() == "text/html":
                content = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return content.decode(charset, errors="replace")

    def get_results(self) -> None:
        '''
        Prints ingestion processing results.
        '''
        print("📊 Bronze Summary:")
        print(f"Total: {self.total} | Extracted: {self.extracted} | Failed: {self.failed}")
