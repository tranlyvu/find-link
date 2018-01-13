from sqlalchemy import Column, Integer, String, DateTime, text, ForeignKey, func, create_engine
from sqlalchemy.ext.declarative import declarative_base
from configparser import ConfigParser
import re
from requests import get, HTTPError
from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base() #metadata

def get_database_url():
    config = ConfigParser()
    try:
        config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'wikilink.ini'))
    except Exception as e:
        print(str(e))

    try:
        connection = config.get('database', 'connection')
    except Exception as e:
        print(str(e), 'could not read from configuration file')
        sys.exit()
    return connection

def update_page_if_not_exists(url):
    """ insert into table Page if not exist

    :param url:
    :return: null
    """

    page_list = session.query(Page).filter(Page.url == url).all()
    if page_list.len() == 0:
        existed_url.add(url)
        page = Page(url=url)
        session.add(page)
        session.commit()


def update_link(from_page_id, to_page_id, no_of_separation):
    """ insert into table Link if link has not existed

    :param from_page_id:
    :param to_page_id:
    :param no_of_separation:
    :return: null
    """

    link_between_2_pages = session.query(Link).filter(Link.from_page_id == from_page_id,
                                                      Link.to_page_id == to_page_id).all()
    if link_between_2_pages.len() == 0:
        link = Link(from_page_id=Link.from_page_id,
                    to_page_id=to_page_id,
                    number_of_separation = no_of_separation)
        session.add(link)
        session.commit()

class Page(Base):
    __tablename__ = 'page'

    id = Column(Integer(), primary_key=True)
    url = Column(String(225))
    created = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return "<Page(page_id = '%s', url ='%s', created='%s')>" %(self.page_id, self.url, self.created)

class Link(Base):
    __tablename__ = 'link'

    id = Column(Integer, primary_key=True)
    from_page_id = Column(Integer, ForeignKey('page.id'))
    to_page_id = Column(Integer, ForeignKey('page.id'))
    number_of_separation = Column(Integer, nullable=False)
    created = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return "<Link(from_page_id='%s', to_page_id='%s', number_of_separation='%s', created='%s')>" % (
                     self.from_page_id, self.to_page_id, self.number_of_separation, self.created)

class WikiLink:
    def __init__(self, starting_url, ending_url, limit = 6):

        connection = get_database_url()
        engine = create_engine(connection, echo=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()  # having conversation with database

        self.limit = limit
        self.starting_url = starting_url
        self.ending_url = ending_url
        self.found = False
        self.number_of_separation = 0

        self.data_handle = DataHandle()

        # update page for both starting and ending url
        self.data_handle.update_page_if_not_exists(starting_url)
        self.data_handle.update_page_if_not_exists(ending_url)

        # update link for starting_url, no of separation between 1 url to itself is zero of course
        self.starting_id = self.session.query(Page.id).filter(Page.url == starting_url).all()
        self.data_handle.update_link(self.starting_id[0], self.starting_id[0], 0)

        # update link for ending_url, no of separation between 1 url to itself is zero of course
        self.ending_id = self.session.query(Page.id).filter(Page.url == ending_url).all()
        self.data_handle.update_link(self.ending_id[0], self.ending_id[0], 0)


    def search(self):
        """ print smallest number of separation

        :return: null
        """

        separation = self.session.query(Link.number_of_separation).filter(
                                    Link.from_page_id ==  self.starting_id,
                                    Link.to_page_id == self.ending_id).first()
        if separation != 0:
            self.number_of_separation = separation
            self.found = True

        while self.found is False:
            self.found = self.data_handle.retrieve_data(self.starting_url, self.ending_url, self.number_of_separation)
            if self.number_of_separation > self.limit:
                print ("No solution within limit! Consider to raise the limit.")
                return
            self.number_of_separation += 1

        print ("Smallest number of separation is " + str(self.number_of_separation))

    def print_links(self):
        """ Print all the links between starting and ending urls

        :return: null
        """

        if self.found is False:
            self.search()

        list_of_links = [self.ending_url]

        while self.starting_url not in list_of_links:
            # retrieve entry in Page with current url
            current_url_id = self.session.query(Page.id).filter(Page.url == self.ending_url).first()

            # retrieve the the shortest path to the current url using id
            min_separation = self.session.query(func.min(Link.number_of_separation)). \
                filter(Link.to_page_id == current_url_id[0])

            # retrieve all the id of pages which has min no of separation to current url
            from_page_id = self.session.query(Link.from_page_id).filter(Link.to_page_id == current_url_id[0],
                                                                   Link.number_of_separation == min_separation)

            #
            url = self.session.query(Page.url).filter(Page.id == from_page_id[0]).first()
            if url[0] not in list_of_links:
                list_of_links.append(url[0])

        list_of_links.reverse()

        for x in list_of_links:
            print(x)



def main():
    NEW_DB_NAME = 'wikilink'
    DB_CONN_FORMAT = get_database_url() 
    engine = create_engine(DB_CONN_FORMAT, echo = True)
    engine.execute("CREATE DATABASE IF NOT EXISTS %s" % NEW_DB_NAME)
    wikilink_engine =  create_engine(DB_CONN_FORMAT + "/" + NEW_DB_NAME, echo = True)
    # If table don't exist, Create.
    if not wikilink_engine.dialect.has_table(wikilink_engine, 'link'):
        if not wikilink_engine.dialect.has_table(wikilink_engine, 'page'):  
            Base.metadata.create_all(wikilink_engine)


if __name__ == "__main__": main()

