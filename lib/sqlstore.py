"""
This module consolidates Database access for this project.
"""

import logging
import os
import sqlite3
from sqlalchemy import Column, Integer, Text, create_engine, ForeignKey, Float, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Action add means it will add the amount to the account in transfer
action_add = ["ShrsOut", "Div", "DivX", "XOut", "SellX", "Sell"]
# Action sub means it will subtract the amount from the account in transfer
action_sub = ["ShrsIn", "BuyX", "Buy"]

Base = declarative_base()


class Bank(Base):
    """
    Table containing bank information
    """
    __tablename__ = "banks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)


class Account(Base):
    """
    Account information related to the bank.
    """
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bank_id = Column(Integer, ForeignKey("banks.id"))
    name = Column(Text, nullable=False)
    number = Column(Text)
    type = Column(Text, nullable=False)
    code = Column(Text, nullable=False, unique=True)
    balance = Column(Float)
    bank = relationship("Bank", foreign_keys=[bank_id], backref="account")


class Transaction(Base):
    """
    Transaction information.
    """
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    account = relationship("Account", foreign_keys=[account_id], backref="account")
    action = Column(Text)
    amount = Column(Float, nullable=False)
    category = Column(Text)
    commission = Column(Float)
    date = Column(Text)
    master_id = Column(Integer, ForeignKey("transactions.id"))
    # master = relationship("Transaction", foreign_keys=[master_id], backref="split")
    memo = Column(Text)
    name = Column(Text)
    payee = Column(Text)
    price = Column(Float)
    quantity = Column(Float)
    reconciled = Column(Text)
    transfer_id = Column(Integer, ForeignKey("accounts.id"))
    transfer = relationship("Account", foreign_keys=[transfer_id], backref="transfer")


class DirectConn:
    """
    This class will set up a direct connection to the database. It allows to reset the database,
    in which case the database will be dropped and recreated, including all tables.
    """

    def __init__(self, config):
        """
        To drop a database in sqlite3, you need to delete the file.
        """
        self.db = config['Main']['db']
        self.dbConn = ""
        self.cur = ""

    def _connect2db(self):
        """
        Internal method to create a database connection and a cursor. This method is called during object
        initialization.
        Note that sqlite connection object does not test the Database connection. If database does not exist, this
        method will not fail. This is expected behaviour, since it will be called to create databases as well.

        :return: Database handle and cursor for the database.
        """
        logging.debug("Creating Datastore object and cursor")
        db_conn = sqlite3.connect(self.db)
        # db_conn.row_factory = sqlite3.Row
        logging.debug("Datastore object and cursor are created")
        return db_conn, db_conn.cursor()

    def rebuild(self):
        # A drop for sqlite is a remove of the file
        try:
            os.remove(self.db)
            logging.info("Database {db} will be recreated".format(db=self.db))
        except FileNotFoundError:
            logging.info("New database {db} will be created".format(db=self.db))
        # Reconnect to the Database
        self.dbConn, self.cur = self._connect2db()
        # Use SQLAlchemy connection to build the database
        conn_string = "sqlite:///{db}".format(db=self.db)
        engine = set_engine(conn_string=conn_string)
        Base.metadata.create_all(engine)


def init_session(db, echo=False):
    """
    This function configures the connection to the database and returns the session object.

    :param db: Name of the sqlite3 database.

    :param echo: True / False, depending if echo is required. Default: False

    :return: session object.
    """
    conn_string = "sqlite:///{db}".format(db=db)
    engine = set_engine(conn_string, echo)
    session = set_session4engine(engine)
    return session


def set_engine(conn_string, echo=False):
    engine = create_engine(conn_string, echo=echo)
    return engine


def set_session4engine(engine):
    session_class = sessionmaker(bind=engine)
    session = session_class()
    return session

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}
