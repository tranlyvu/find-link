from database.data_handle import DataHandle
from settings import my_user, my_password, my_host
from searcher.searcher import Searcher
import MySQLdb

from sqlalchemy import creat_engine
from sqlalchemy.orm import sessionmaker

engine = creat_engine('sqlite:///:memory:')
Session = session(bind = engine)
session = Session()


class FindLink:
    def __init__(self, starting_url, ending_url, limit = 6):
        """ Main class of the application

        Parameters
        --------------
        starting_url: string, wiki page in the form of '/wiki/something'

        ending_url : string, wiki page in the form of '/wiki/something'

        Returns
        --------------
        self : object
           Returns self.
        """

        self.limit = limit
        self.starting_url = starting_url
        self.ending_url = ending_url

        # insert starting page into 'page' table
        page = Page(url = starting_url)
        session.add(page)
        session.commit()

        # insert link from 'starting_url' to 'starting_url' with 0 number of separation
        self.cur.execute("""SELECT id FROM pages WHERE url='%s' """ % (self.starting_url))
        self.starting_url_id = self.cur.fetchone()
        self.data.update_links_table(self.starting_url_id[0], self.starting_url_id[0], 0)

    def search(self):
        """ return out the smallest number of links between 2 given urls

        Parameters
        --------------

        None

        Returns
        --------------

        None
        """

        self.number_of_separation = 1
        self.found = self.data.retrieveData(self.starting_url, self.ending_url, self.number_of_separation)

        while self.found == False:
            self.number_of_separation += 1
            if self.number_of_separation > self.limit:
                print ("Number of separation is exceeded number of limit. Stop searching!")
                return
            self.found = self.data.retrieveData(self.starting_url, self.ending_url, self.number_of_separation)

        print ("Smallest number of separation is " + str(self.number_of_separation))

    def print_links(self):
        """ return the links between 2 given urls

        Parameters
        --------------

        None

        Returns
        --------------
        prints links between 2 given urls
        """
        if self.number_of_separation > self.limit or self.found == False:
            print ("No solution within limit!")
            return
        my_search = searcher(self.starting_url, self.ending_url)
        my_list = [self.ending_page] + searcher.list_of_links()
        my_list.reverse()
        for x in my_list:
            print x
