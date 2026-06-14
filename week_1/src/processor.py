import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, model_validator, ValidationInfo, ValidationError
from bs4 import BeautifulSoup
from typing_extensions import Self

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s |%(levelname)s |%(message)s"
)


class Processor:
    '''
    Processor class used in data processing and transformation.
    Uses pydantic to create a BaseModel class for automatic validation.
    '''
    class JobListing(BaseModel):
        source_id: str | None = Field(description="ID from HTML meta tag")
        job_title: str | None
        description: str | None
        company: str | None

        @model_validator(mode="after")
        def validate_fields(self, info: ValidationInfo) -> Self:
            filename = f"{info.context.get("filename")}.html"
            missing = []

            if not self.source_id:
                missing.append("source_id")
            if not self.job_title:
                missing.append("job_title")
            if not self.description:
                missing.append("description")
            if not self.company:
                missing.append("company")

            if missing:
                fields = f"{', '.join(missing)}"
                raise ValueError(f"⚠️  Missing {fields} in: {filename}")
            return self

    def __init__(self, input_dir: str, output_dir: str) -> None:
        self.processed = 0
        self.skipped = 0
        self.total = 0
        self.src_dir = Path(input_dir)
        self.out_dir = Path(output_dir)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def process_all_html(self):
        print("(week_1) week_1 [week1] python main.py process")
        print("🥈 Silver:...")

        for path in self.src_dir.glob("*.html"):
            filename = path.stem
            html = path.read_text(encoding="utf-8")
            soup = BeautifulSoup(html, "html.parser")
            try:
                # Extract ID
                source_id = soup.find("meta", attrs={"property": "og:url"})
                source_id = source_id["content"].split("/")[-1] if source_id else None
                # Extract job title
                title = soup.find(attrs={"data-automation": "job-detail-title"})
                title = title.get_text(strip=True) if title else None
                # Extract company
                company = soup.find(attrs={"data-automation": "advertiser-name"})
                company = company.get_text(strip=True) if company else None
                # Extract description
                description = soup.find(attrs={"data-automation": "jobAdDetails"})
                description = description.get_text(" ", strip=True) if description else None
                job = self.JobListing.model_validate(
                    {
                        'source_id': source_id,
                        'job_title': title,
                        'company': company,
                        'description': description
                    },
                    context={"filename": filename}
                )
                destination = self.out_dir / f"{filename}.json"
                with destination.open("w", encoding="utf-8") as f:
                    f.write(job.model_dump_json(indent=2))
                logging.info(f"✅ Processed: {filename}.html")
                self.processed += 1
            except ValidationError as e:
                msg = e.errors()[0].get("ctx", {}).get("error")
                logging.warning(msg)
                self.skipped += 1
            except Exception as e:
                logging.error(e)
                self.skipped += 1
                return
            self.total += 1

        print("")
        self.get_results()

    def get_results(self) -> None:
        '''
        Prints ingestion processing results.
        '''
        print("📊 Silver Summary:")
        print(f"Total: {self.total} | Processed: {self.processed} | Skipped: {self.skipped}")
