import csv
import time
from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Dataset(Base):
    __tablename__ = "dataset"
    id = Column(Integer, primary_key=True)
    text = Column(String(255), nullable=False)  # 确保这里的长度和数据库中的字段长度一致
    label = Column(Integer, nullable=False)
    source = Column(Integer)
    create_time = Column(BigInteger)

DATABASE_URI = "postgresql://bn_mlflow:bn_mlflow@10.43.196.160/bn_mlflow"
CSV_FILE_PATH = "/root/data/comments.csv"
engine = create_engine(DATABASE_URI)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

with open(CSV_FILE_PATH, "r", encoding="utf-8") as csvfile:
    csv_reader = csv.DictReader(csvfile)
    bulk_data = []
    for row in csv_reader:
        dataset_entry = Dataset(
            text=row["reply"][:255],  # 截断文本到255字符
            label=int(row["is_troll"]),
            source=0,
            create_time=int(time.time())
        )
        bulk_data.append(dataset_entry)

    session.bulk_save_objects(bulk_data)

session.commit()
session.close()
