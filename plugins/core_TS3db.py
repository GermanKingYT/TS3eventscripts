from ts3tools import ts3tools
import pymysql

name = 'core.TS3db'

base = None
config = None


def setup(ts3base):
    global base
    base = ts3base
    base.register_class(name, core_TS3db)


class core_TS3db:
    # [TODO: better methods for a better life without sql commands]

    def __init__(self, ts3base):
        """
        Initializes a TS3db object.
        """
        self.base = ts3base
        self.config = ts3tools.get_global_config(name)
        # placeholders
        self.connection = None
        self.cursor = None
        if self.connect():
            self.base.debprint('[MySQL] Database connection established to host "' + self.config['MySQL']['host'] + '"!')

    def connect(self):
        """
        Internal method: Connects to a MySQL server and initializes the cursor.
        Do not use it because it's called at database core init automatically!
        """
        try:
            self.connection = pymysql.connect(self.config['MySQL']['host'], self.config[
                                              'MySQL']['user'], self.config['MySQL']['pass'], self.config['MySQL']['db'])
        except pymysql.Error as e:
            self.base.debprint("[MySQL] Error %d: %s" % (e.args[0], e.args[1]))
            self.connection = False
            return False
        if self.connection is not False:
            self.cursor = self.connection.cursor()
            return True
    # database schema
    # note: there are no global database tables because therefore you can use config files ;)
    # [instance_name]                       -> instance config
    # [instance_name]_[plugin_name]         -> general plugin table
    # [instance_name]_[plugin_name]_table   -> more plugin tables

    def get_table_name(self, plugin_name, table_name=None):
        """
        Constructor for table names.
        Please note that the table with the returned table name needn't to be in the database!
        """
        if table_name is not None:
            return (self.base.config['id'] + '_' + plugin_name.replace('.', '-') + '_' + table_name).lower()
        else:
            return (self.base.config['id'] + '_' + plugin_name.replace('.', '-')).lower()

    def create_table(self, plugin_name, columns, table_name=None):
        """
        If not exists, creates a table with given name and columns.

        @plugin_name    name of plugin (unique name)
        @columns        list of columns, each column is a list with two elements: the column name and the column type (e.g. [['one', 'INT'], ['two', 'TEXT'], ['three', 'VARCHAR(42)']])
        @(table_name)   name of the "sub" table
        """
        columnstring = ' (`id` INT NOT NULL AUTO_INCREMENT, PRIMARY KEY (`id`)'
        for column in columns:
            columnstring += ', `' + column[0] + '` ' + column[1]
        columnstring += ')'
        if table_name is not None:
            try:
                self.cursor.execute('CREATE TABLE IF NOT EXISTS `' + self.get_table_name(plugin_name, table_name) + '`' + columnstring + ';')
                return True
            except pymysql.Error as e:
                self.base.debprint(
                    '[MySQL] Error %d: %s' % (e.args[0], e.args[1]))
                return False
        else:
            try:
                self.cursor.execute('CREATE TABLE IF NOT EXISTS `' + self.get_table_name(plugin_name) + '`' + columnstring + ';')
                return True
            except pymysql.Error as e:
                self.base.debprint(
                    '[MySQL] Error %d: %s' % (e.args[0], e.args[1]))
                return False

    def execute(self, command):
        """
        Manually executes commands.
        Note: If you don't know how to do, please use the pre-formatted command methods!
        """
        try:
            self.cursor.execute(command)
            self.connection.commit()
            return True
        except pymysql.Error as e:
            self.base.debprint('[MySQL] Error: %d: %s' %
                               (e.args[0], e.args[1]))
            return False

    def fetch_one(self):
        return self.cursor.fetchone()

    def fetch_all(self):
        return self.cursor.fetchall()