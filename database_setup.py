import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    username = Column(String(250), primary_key=True)
    password = Column(String(250), nullable=False)
    bill = Column(Numeric(12, 2), nullable=False)

class Campaign(Base):
    __tablename__ = 'campaign'

    id = Column(Integer, primary_key=True)
    category = Column(String(80), nullable=False)
    budget = Column(Numeric(12, 2), nullable=False)
    min_bid = Column(Numeric(12, 2), nullable=False)
    max_bid = Column(Numeric(12, 2), nullable=False)
    ad_url = Column(String(250), nullable=False)
    description = Column(String(2000))
    total_show = Column(Integer, nullable=False)
    total_clicks = Column(Integer, nullable=False)
    current_cost = Column(Numeric(12, 2), nullable=False)
    active = Column(Boolean, nullable=False)
    username = Column(String(250), nullable=False)

engine = create_engine('sqlite:///adserver.db')


Base.metadata.create_all(engine)
