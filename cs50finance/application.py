import os
import sys

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime


from helpers import apology, login_required, lookup, usd

db = SQL("sqlite:///finance.db")

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")



@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Update stock price before showing
    # Search stock => lookup price => Update price of those stock
    # Get tickers
    tickers = db.execute("SELECT DISTINCT ticker FROM transac WHERE user = :user", user = session["user_id"])

    grand_total = 0
    print("\n\n")
    print(tickers, file=sys.stderr)

    # Empty portfolio list
    portfolio = []
    # Get individual ticker
    for ticker in tickers:
        ticker_company = ticker['ticker']
        print("\n\nticker_company")
        print(ticker_company, file=sys.stderr)
        new_price = lookup(ticker_company)
        new_price = float(new_price['price'])
        print(new_price, file=sys.stderr)

        # # Update price after every refresh
        # db.execute("UPDATE transac SET price = :new_price WHERE ticker = :ticker", new_price=new_price, ticker = ticker_company)

        # Calculate grand_total given the newest price of stock => calculate grand_total later on
        total_share_of_each_stock = db.execute("SELECT SUM(shares) as total_share FROM transac WHERE ticker = :ticker AND user=:user",
                                    ticker=ticker_company, user = session["user_id"])
        # Parse the value
        total_share_of_each_stock = total_share_of_each_stock[0]['total_share']

        # Total value of each stock
        sub_total1 = total_share_of_each_stock * new_price

        # Total value of all stocks incremental in each loop
        grand_total = sub_total1 + grand_total

        print("\n\nsub_total1")
        print(sub_total1, file=sys.stderr)

        print("\n\ntotal_share_of_each_stock")
        print(total_share_of_each_stock, file=sys.stderr)

        # Get information of each stock
        stock_info = db.execute("SELECT ticker, name, CAST(SUM(shares) as int) as shares, price, ROUND(SUM(shares)*price,2) as total "
                            "FROM transac WHERE user = :user AND ticker=:ticker GROUP BY name", user = session["user_id"], ticker=ticker_company)

        # Change the element "price" to new price as we refresh the page
        stock_info[0]['price'] = new_price

        # Change the "total" element to new total with newest price
        stock_info[0]['total'] = round(new_price*int(stock_info[0]['shares']),2)

        # Append each stock_info to portfolio
        # stock_info [{'ticker':'QQQ', 'name':'Invesco QQQ Trust', 'shares': 1, 'price': 244.24, 'total':244.24}]
        # portfolio will eventually looks like this portfolio [{'ticker': 'AAPL', 'name': 'Apple, Inc.', 'shares': 10, 'price': 349.72, 'total': 3497.2}, {'ticker': 'QQQ', 'name': 'Invesco QQQ Trust', 'shares': 1, 'price': 244.24, 'total': 244.24}, {'ticker': 'TQQQ', 'name': 'ProShares UltraPro QQQ', 'shares': 2, 'price': 93.92, 'total': 187.84}, {'ticker': 'ROKU', 'name': 'Roku, Inc.', 'shares': 10, 'price': 128.5, 'total': 1285.0}, {'ticker': 'BA', 'name': 'The Boeing Co.', 'shares': 14, 'price': 187.02, 'total': 2618.28}, {'ticker': 'ZM', 'name': 'Zoom Video Communications, Inc.', 'shares': 15, 'price': 243.48, 'total': 3652.2}]
        portfolio.append(stock_info[0])

        print("\n\nstock_info")
        print(stock_info, file=sys.stderr)


    print("\n\ngrand_total")
    print(grand_total, file=sys.stderr)


    # # Type: list of dictionary
    # # Total here is computed using the latest price, the original total was not affected
    # portfolio = db.execute("SELECT ticker, name, CAST(SUM(shares) as int) as shares, price, ROUND(SUM(shares)*price,2) as total "
    #                         "FROM transac WHERE user = :user GROUP BY name", user = session["user_id"])

    print("\n\nportfolio")
    print(portfolio, file=sys.stderr)



    # Calculate the total cost so far
    total_cost = db.execute("SELECT SUM(total) as total FROM transac WHERE user = :user", user=session["user_id"])
    total_cost = total_cost[0]['total']
    print("\n\ntotal_cost")
    print(total_cost, file=sys.stderr)


    # Get total cash left
    cash_left = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
    cash_left = round(cash_left[0]['cash'],2)
    print("\n\ncash_left")
    print(cash_left, file=sys.stderr)


    # Calculate grand_total given the newest price of stock
    total_value_of_current_portfolio = grand_total + cash_left
    print("\n\ntotal_value_of_current_portfolio")
    print(total_value_of_current_portfolio, file=sys.stderr)

    # grand_total = cash_left +

    # # Portfolio is A LIST of mutiple dictionaries => port[0]
    # l = portfolio[0]
    # row = []

    # symbol, name, shares, price, total = [], [], [], [], []
    # for i in l:
    #     symbol = symbol.append(i['ticker'])
    #     name = name.append(i['name'])
    #     shares = shares.append(i['share'])
    #     price = price.append(i['price'])
    #     total = total.append(price * shares)

    print("\n\n")
    print(portfolio, file=sys.stderr)



    return render_template("index.html", portfolio=portfolio, cash_left=cash_left, total_value_of_current_portfolio=round(total_value_of_current_portfolio,2))
    # return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    elif request.method == "POST":
        ticker = request.form.get("symbol")
        shares = request.form.get('shares')

        # shares can't be negative or 0 or fractioinal or text
        if shares.isdigit() and int(shares)>0 and float(shares)%int(shares) == 0:
            ticker_info = lookup(ticker)
            # If can't find the ticker
            if not ticker_info:
                return apology("Invalid Ticker")

            else:
                name, ticker, price = ticker_info['name'], ticker_info['symbol'], ticker_info['price']
                timestamp = datetime.today()
                user = session["user_id"]

                # Check how much cash user has left
                # Type: list of dictionary [{'Cash': 5000000}]
                cash = db.execute("SELECT cash FROM users WHERE id = :user", user=user)
                cash = float(cash[0]['cash']) # Only one result so convert that one to the float


                # Check how much is the transaction
                cash_required = price * int(shares)

                # If enough cash to buy stocks
                if (cash >= cash_required):
                    # Enter input into trasac table
                    db.execute("INSERT INTO transac(ticker, name, shares, price, date, user, total) "
                                "VALUES(:ticker, :name, :shares, :price, :date, :user, :total)",
                                ticker=ticker, name=name, shares=shares, price=price, date=timestamp, user=user, total=cash_required)

                    # Reduce the cash of the user after bought
                    new_cash = cash - cash_required

                    # Update the cash
                    db.execute("UPDATE users SET cash = :new_cash WHERE id = :user", new_cash=new_cash, user=user)

                    # TODO: route to main page
                    return redirect("/")

                else:
                    return apology("Not enough cash")

        else:
            return apology("Shares has to be an integer number greater than 0")

    # return apology(str(new_cash))


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    all_transactions = db.execute("SELECT ticker, shares, price, date FROM transac WHERE user=:user", user = session['user_id'])
    print("\n\nall_transactions")
    print(all_transactions, file=sys.stderr)
    return render_template("history.html", all_transactions=all_transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to HomePage
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    elif request.method == "POST":
        # get ticker after hitting submit on html
        ticker = request.form.get("quote")
        ticker_info = lookup(ticker)
         # If can't find the ticker
        if not ticker_info:

            return apology("Invalid Ticker")
        else:
            name, price, symbol = ticker_info['name'], usd(ticker_info['price']), ticker_info['symbol']
            return render_template("quoted.html", name=name, price=price, symbol=symbol)


        # return {
        #     "name": quote["companyName"],
        #     "price": float(quote["latestPrice"]),
        #     "symbol": quote["symbol"]
        # }


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == 'GET':
        return render_template("register.html")

    elif request.method == 'POST':
        un = request.form.get('username')
        pw = request.form.get('password')
        cf = request.form.get('confirmation')


        un_exist = db.execute("SELECT username FROM users WHERE username = (:un)", un=un)

        # username already taken
        if (un_exist):
            return apology("Username was already taken")

        # username can't be blank
        elif not un:
            return apology("Username can't be blank")

        # password can't be blank
        if not pw or not cf:
            return apology("Password can't be blank")

        # password must match
        if pw != cf:
            return apology("Passwords are not matched")

        # hash password
        hs = generate_password_hash(pw, method='pbkdf2:sha256')

        # enter credential to SQL database
        db.execute('INSERT INTO users(username, hash) VALUES (:un, :hs)', un=un, hs=hs)
        return redirect("/")

    # return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

     # Get all stocks of user having more than quantity of 1
    distinct_ticker_list = db.execute("SELECT DISTINCT ticker FROM transac WHERE user=:user", user=session['user_id'])
    print("\n\ndistinct_ticker_list")
    print(distinct_ticker_list, file=sys.stderr)

    # Use this list of dict for both GET & POST - check number of shares available to sell
    ticker_input = []

    if request.method == "GET":


        # Get the name of the ticker having shares > 0
        for ticker_dict in distinct_ticker_list:

            # sub_dict containing ticker and share numbers to append to ticker_input
            ticker_n_shares = {}

            ticker = ticker_dict['ticker']
            print("\n\n")
            print(ticker, file=sys.stderr)

            shares = db.execute("SELECT SUM(shares) AS shares FROM transac WHERE ticker=:ticker", ticker=ticker)
            print("\n\n")
            print(shares, file=sys.stderr)

            # get shares out of list format: [{'shares': 21}]
            shares = shares[0]['shares']
            print("\n\n")
            print(ticker, shares, file=sys.stderr)

            # if number of shares holding > 0 => add to the select menu
            if shares > 0:
                # add to the sub_dict  ticker_n_shares first
                ticker_n_shares[ticker] = shares
                ticker_input.append(ticker_n_shares)

        print("\n\nticker_input")
        print(ticker_input, file=sys.stderr)

        return render_template("sell.html", ticker_input=ticker_input)




    # If it is a post request
    elif request.method == "POST":

        # Get shares_to_sell & symbol input from HTML
        ticker = request.form.get("symbol")
        shares_to_sell = int(request.form.get("shares"))

        print("\n\nticker, shares")
        print(ticker, shares_to_sell, file=sys.stderr)

        # Check number of shares user has in their portfolio
        shares_holding_and_name = db.execute("SELECT name, SUM(shares) AS shares FROM transac WHERE ticker = :ticker AND user = :user",
                                    ticker = ticker, user = session['user_id'])


        print("\n\nshares_holding_and_name of current stock")
        print(shares_holding_and_name, file=sys.stderr)

        # Get shares_holding out of the list [{'name': 'Apple, Inc.', 'shares': 11}]
        shares_holding = shares_holding_and_name[0]['shares']

        # Get name out of the list [{'name': 'Apple, Inc.', 'shares': 11}]
        name = shares_holding_and_name[0]['name']

        print("\n\nExtract name of the stock")
        print(name, file=sys.stderr)

        print("\n\nExtract shares number out of shares_holding")
        print(shares_holding, file=sys.stderr)

        # If try to sell more than what currently own => error
        if shares_to_sell > int(shares_holding):
            return apology("Can't sell more than what you currently own " + ticker + ":" + str(shares_holding))
        else:
            # First need to find a new price when sold
            new_price = lookup(ticker)['price']

            # Amount collecting from the sell
            collecting_amount = shares_to_sell*new_price

            # Add to SQL table with sell
            db.execute("INSERT INTO transac (ticker, name, shares, price, date, user, total) VALUES"
                        "(:ticker, :name, :shares, :price, :date, :user, :total)", ticker=ticker,
                        name=name, shares = -shares_to_sell, price=new_price, date=datetime.today(),
                        user=session['user_id'], total=collecting_amount)

            # Get cash on hand
            cash_on_hand = db.execute("SELECT cash FROM users WHERE id=:user", user = session['user_id'])
            print("\n\ncash_on_hand")
            print(cash_on_hand, file=sys.stderr)

            # Get cash_on_hand out of the list [{'cash': 7565.200000000001}]
            cash_on_hand = cash_on_hand[0]['cash']

            # Add that selling amount to cash
            db.execute("UPDATE users SET cash=:new_cash WHERE id=:user", new_cash=cash_on_hand + collecting_amount,
                        user=session['user_id'])

            return redirect("/")

        return apology("Wait for implementing")


    # if request.method == "GET":
    #     return render_template("buy.html")
    # elif request.method == "POST":
    #     ticker = request.form.get("symbol")
    #     shares = request.form.get('shares')

    #     # shares can't be negative or 0 or fractioinal or text
    #     if shares.isdigit() and int(shares)>0 and float(shares)%int(shares) == 0:
    #         ticker_info = lookup(ticker)
    #         # If can't find the ticker
    #         if not ticker_info:
    #             return apology("Invalid Ticker")

    #         else:
    #             name, ticker, price = ticker_info['name'], ticker_info['symbol'], ticker_info['price']
    #             timestamp = datetime.today()
    #             user = session["user_id"]

    #             # Check how much cash user has left
    #             # Type: list of dictionary [{'Cash': 5000000}]
    #             cash = db.execute("SELECT cash FROM users WHERE id = :user", user=user)
    #             cash = float(cash[0]['cash']) # Only one result so convert that one to the float


    #             # Check how much is the transaction
    #             cash_required = price * int(shares)

    #             # If enough cash to buy stocks
    #             if (cash >= cash_required):
    #                 # Enter input into trasac table
    #                 db.execute("INSERT INTO transac(ticker, name, shares, price, date, user, total) "
    #                             "VALUES(:ticker, :name, :shares, :price, :date, :user, :total)",
    #                             ticker=ticker, name=name, shares=shares, price=price, date=timestamp, user=user, total=cash_required)

    #                 # Reduce the cash of the user after bought
    #                 new_cash = cash - cash_required

    #                 # Update the cash
    #                 db.execute("UPDATE users SET cash = :new_cash WHERE id = :user", new_cash=new_cash, user=user)

    #                 # TODO: route to main page
    #                 return redirect("/")

    #             else:
    #                 return apology("Not enough cash")

    #     else:
    #         return apology("Shares has to be an integer number greater than 0")





        # return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
