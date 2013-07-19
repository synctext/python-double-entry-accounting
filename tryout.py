"""\
We'll experiment with a ledger of double entry accounting.

Persistance will be in memory. Each time all transactions have to be replayed.

"""
from decimal import Decimal as D

DEFAULT_CURRENCIES = ['EUR']
FEE = D(0.006)

class Book(object):
    
    def __init__(self):
        """ """
        self._accounts = []
        self._transactions = []
        # Index accounts
        self._index = {}
    
    def add_account(self, account, currencies=None): #, parent=None
        """ """
        # Code should be unique (for now)
        assert account._code not in self._index
        # Enable currencies
        for key in currencies or DEFAULT_CURRENCIES:
            account.enable_currency(key)
        # Store
        self._index[account._code] = account
        self._accounts.append(account)
    
    def add_journal(self, journal):
        """ """
        # First try if it works out
        # validate
        tmp_deb = {}
        tmp_cred = {}
        for record in journal:
            tmp_deb.setdefault(record[3], 0)
            tmp_cred.setdefault(record[3], 0)
            tmp_deb[record[3]] += record[1]
            tmp_cred[record[3]] += record[2]
        # validate
        for asset in tmp_deb:
            assert tmp_deb[asset] == tmp_cred[asset]
        # commit
        for record in journal:
            record[0].process_record(record)
        # finally
        self._transactions.append(journal)
    
    def get_account(self, code):
        return self._index[code]

class Account(object):
    """The most basic part of accounting """
    TYPE_ASSET = 0
    TYPE_LIABILITY = 1
    TYPE_EQUITY = 2
    TYPE_INCOME = 3
    TYPE_EXPENSE = 4
    TYPES = [TYPE_ASSET,
             TYPE_LIABILITY,
             TYPE_EQUITY,
             TYPE_INCOME,
             TYPE_EXPENSE,]
    def __init__(self, name, type_=TYPE_ASSET, code=None):
        """ """
        self._name = name
        self._type = type_
        self._code = code
        # Validate
        assert type_ in Account.TYPES
        # Values
        self._balance = {}
        #self._credits = {'EUR': D('0')}
        self._records = []
        # Recursive
        #self_children = []
    
    def enable_currency(self, currency):
        self._balance[currency] = D('0')
    
    def process_record(self, record):
        """ """
        assert record[0] is self
        self._records.append((record[0], record))
        # commit
        if self._type in (Account.TYPE_ASSET, Account.TYPE_EXPENSE):
            # Debit in Asset or Expense will increase the balance
            self._balance[record[3]] += record[1] - record[2]
        else:
            # the other way around for other types
            self._balance[record[3]] -= record[1] - record[2]
        
    def __str__(self):
        """ """
        return "%04s %-16s" % (self._code or "", self._name)


class Journal(object):
    """A journal is a collection of accounting records. Each record debits or 
    credits a specific account.
    There are always an even amount of records in a Journal. All journal entries 
    add up to 0; the sum of debit and credt posts is equal.
    """
    def __init__(self):
        self._records = []
        
    def add_record(self, account, amount_debit, amount_credit, asset,
                   description=''):
        """ """
        # Validate
        self._records.append((account, amount_debit, amount_credit, asset, description))
    def __iter__(self):
        return iter(self._records)
    
def book2balance(book, currencies):
    for asset in currencies:
        print asset
        for account in book._accounts:
            if asset in account._balance:
                print account, "%10.4f" % account._balance[asset]

if __name__ == "__main__":
    """
    The script:
    * create a user account A: liability
    * create a bank account B: asset
    * create a journal for a deposit of EUR 500
    ** debit B for 500 EUR (bank owes us)
    ** credit A for 500 EUR
    * print balance report
    """
    book = Book()
    a = Account('Account A', Account.TYPE_LIABILITY, '1400')
    b = Account('ING7197307', Account.TYPE_ASSET, '1200')
    book.add_account(a, ['EUR', 'BTC'])
    book.add_account(b)
    # Deposit EUR 500
    j = Journal()
    j.add_record(b, D('500'), 0, 'EUR', 'deposit 500 eur to user A')
    j.add_record(a, 0, D('500'), 'EUR', 'deposit 500 eur to user A')
    book.add_journal(j)
    book2balance(book, ['EUR'])
    
    """
    * create a user account C: liability
    * create a bitcoin account D: asset
    * create a journal for a deposit of BTC 10 from C to D
    ** debit D for 10 BTC (ledger owes us)
    ** credit C for 10 BTC
    * print balance report
    """
    c = Account('Account C', Account.TYPE_LIABILITY, '1401')
    d = Account('Hotwallet', Account.TYPE_ASSET, '1201')
    book.add_account(c, ['EUR', 'BTC'])
    book.add_account(d, ['BTC'])
    # Deposit BTC 10
    j = Journal()
    j.add_record(d, D('10'), 0, 'BTC', 'deposit 10 btc to user C')
    j.add_record(c, 0, D('10'), 'BTC', 'deposit 10 btc to user C')
    book.add_journal(j)
    book2balance(book, ['BTC'])
    
    """
    Exchange EUR and BTC between A and C
    
    (this should be done with 2 orders being placed and reserved)
    (also take taxes in account)
    
    * create a fee account F: asset
    * exchange BTC 4.5 from C to A for 320.85 (70.3 EUR/BTC)
    ** debit C for 4.5 BTC
    ** credit C for 320.85 BTC
    ** debit A for 320.85 BTC
    ** credit A for 4.5 BTC
    ** apply EUR fee to C
    ** apply BTC fee to A
    * print balance report
    """
    f = Account('Exchange fees', Account.TYPE_INCOME, '8400')
    book.add_account(f, ['EUR', 'BTC'])
    # Deposit BTC 10
    j = Journal()
    amount_eur = D(320.85)
    amount_btc = D(4.5)
    j.add_record(c, amount_btc, 0, 'BTC', 'exchange 4.5 BTC')
    j.add_record(c, 0, amount_eur, 'EUR', 'exchange 4.5 BTC')
    j.add_record(a, amount_eur, 0, 'EUR', 'exchange 4.5 BTC')
    j.add_record(a, 0, amount_btc, 'BTC', 'exchange 4.5 BTC')
    j.add_record(c, amount_eur*FEE, 0, 'EUR', 'fee: exchange 4.5 BTC')
    j.add_record(f, 0, amount_eur*FEE, 'EUR', 'fee: exchange 4.5 BTC')
    j.add_record(a, amount_btc*FEE, 0, 'BTC', 'fee: exchange 4.5 BTC')
    j.add_record(f, 0, amount_btc*FEE, 'BTC', 'fee: exchange 4.5 BTC')
    book.add_journal(j)
    book2balance(book, ['EUR', 'BTC'])
