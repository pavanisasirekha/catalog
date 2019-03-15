import sys
import os
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    picture = Column(String(300))


class SwitchCompanyName(Base):
    __tablename__ = 'switchcompanyname'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="switchcompanyname")

    @property
    def serialize(self):
        """Return objects data in easily serializeable formats"""
        return {
            'name': self.name,
            'id': self.id
        }


class SwitchName(Base):
    __tablename__ = 'switchname'
    id = Column(Integer, primary_key=True)
    name = Column(String(350), nullable=False)
    color = Column(String(150))
    price = Column(String(10))
    switchtype = Column(String(250))
    switchcompanynameid = Column(Integer, ForeignKey('switchcompanyname.id'))
    switchcompanyname = relationship(SwitchCompanyName,
                                     backref=backref('switchname',
                                                     cascade='all, delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="switchname")

    @property
    def serialize(self):
        """Return objects data in easily serializeable formats"""
        return {
            'name': self. name,
            'color': self. color,
            'price': self. price,
            'switchtype': self. switchtype,
            'id': self. id
        }

engin = create_engine('sqlite:///switches.db')
Base.metadata.create_all(engin)
