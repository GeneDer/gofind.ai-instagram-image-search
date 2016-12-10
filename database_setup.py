import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(2000), nullable=False)

class Main_image(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    main_image_path = Column(String(2000), nullable=False)
    username = Column(String(2000), nullable=False)

class Segmented(Base):
    __tablename__ = 'segmented'

    id = Column(Integer, primary_key=True)
    segmented_image_path = Column(String(2000), nullable=False)
    classes = Column(String(200), nullable=False)
    cx = Column(Numeric(12, 2), nullable=False)
    cy = Column(Numeric(12, 2), nullable=False)
    w = Column(Numeric(12, 2), nullable=False)
    h = Column(Numeric(12, 2), nullable=False)
    confidence = Column(Numeric(12, 10), nullable=False)
    post_id = Column(Integer, nullable=False)

class Results(Base):
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True)
    segmented_id = Column(Integer, nullable=False)
    image_url = Column(String(2000), nullable=False)
    seller_url = Column(String(2000), nullable=False)
    seller_name = Column(String(200), nullable=False)
    item_name = Column(String(200), nullable=False)
    price = Column(String(200), nullable=False)


engine = create_engine('sqlite:///instagram.db')


Base.metadata.create_all(engine)
