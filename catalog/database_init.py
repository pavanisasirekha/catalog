from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from Data_Setup import *

engine = create_engine('sqlite:///switches.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Delete SwitchesCompanyName if exisitng.
session.query(SwitchCompanyName).delete()
# Delete SwitchName if exisitng.
session.query(SwitchName).delete()
# Delete User if exisitng.
session.query(User).delete()

# Create sample users data
User1 = User(name="Pavani Sasi Rekha",
             email="rekha95379@gmail.com",
             picture='http: //www.enchanting.costarica.com/wp-content/'
                     'uploads/2018/02/jcarvaja17.min.jpg')
session.add(User1)
session.commit()
print ("Successfully Add First User")
# Create sample switch companys
Company1 = SwitchCompanyName(name="LEGRAND",
                             user_id=1)
session.add(Company1)
session.commit()

Company2 = SwitchCompanyName(name="HAVELLS",
                             user_id=1)
session.add(Company2)
session.commit

Company3 = SwitchCompanyName(name="WIPRO",
                             user_id=1)
session.add(Company3)
session.commit()

Company4 = SwitchCompanyName(name="FINOLEX",
                             user_id=1)
session.add(Company4)
session.commit()

Company5 = SwitchCompanyName(name="SIEMENS",
                             user_id=1)
session.add(Company5)
session.commit()

Company6 = SwitchCompanyName(name="ANCHOR",
                             user_id=1)
session.add(Company6)
session.commit()

# Populare a switches with models for testing
# Using different users for switches names year also
Name1 = SwitchName(name="legrand",
                   color="white",
                   price="160",
                   switchtype="modular",
                   switchcompanynameid=1,
                   user_id=1)
session.add(Name1)
session.commit()

Name2 = SwitchName(name="havells",
                   color="brown",
                   price="130",
                   switchtype="two way",
                   switchcompanynameid=2,
                   user_id=1)
session.add(Name2)
session.commit()

Name3 = SwitchName(name="wipro",
                   color="ash",
                   price="100",
                   switchtype="normal",
                   switchcompanynameid=3,
                   user_id=1)
session.add(Name3)
session.commit()

Name4 = SwitchName(name="finolex",
                   color="white",
                   price="90",
                   switchtype="modular",
                   switchcompanynameid=4,
                   user_id=1)
session.add(Name4)
session.commit()

Name5 = SwitchName(name="siemens",
                   color="silver",
                   price="70",
                   switchtype="three pin",
                   switchcompanynameid=5,
                   user_id=1)
session.add(Name5)
session.commit()

Name6 = SwitchName(name="anchor",
                   color="white",
                   price="50",
                   switchtype="normal",
                   switchcompanynameid=6,
                   user_id=1)
session.add(Name6)
session.commit()

print("Your switches database has been inserted!")
