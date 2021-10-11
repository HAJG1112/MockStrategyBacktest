'''
Author: Haisun Grigg
'''
import pandas as pd
class core():
    def __init__(self, starting_capital, debug = True):
        '''Housekeeping'''
        self.debug = True
        '''Starting Conditions'''
        self.starting_capital = starting_capital
        self.invested = []
        self.cash = []
        self.aum = []

        self.invested.append(0) 
        self.cash.append(self.starting_capital)
        self.aum.append(self.cash[0] + self.invested[0])

        '''Winning and losing trade tally to assign win rates to'''
        self.trades_won = 0
        self.trades_lost = 0

        self.portfolio = pd.DataFrame()

    def EnterTrade(self, _slice, amt_to_trade):
        # take a given slice, allocate amount invested and store in self.portfolio
        # negate total amount of amt_to_trade 
        self._debug(f'Enter Trade | Number of assets before Trade: {len(self.portfolio)}')
        _slice.reset_index(inplace = True)
        _slice['amount_invested'] = amt_to_trade
        total_investment = _slice['amount_invested'].sum()

        # Check if we have cash to enter positions
        if total_investment < self.cash[-1]:

            _slice['investment_return'] = _slice['amount_invested'] * (1 + _slice['signal_return']/100)
            _slice.set_index('exit_date', inplace = True)
            self.portfolio = pd.concat([self.portfolio, _slice], axis = 0)
            self._debug(f'Enter Trade | Number of assets: {len(self.portfolio)}')

            # return the amount we are looking to invest
            return total_investment

        else:
            self._debug('unable to trade - no cash')
            return 0

    def TrackPortfolio(self, current_date):
        # apply a mask over those we wish to sell
        try:
            to_sell = self.portfolio.loc[current_date]
            sell_flag = True
        except KeyError:
            self._debug('No matching date')
            sell_flag = False

        # if the mask applied is not empty, trade out of those positions
        if sell_flag == True :
            self._debug('To sell')
            pnl = to_sell.investment_return.sum() - to_sell.amount_invested.sum()

            self.invested.append(self.invested[-1] - to_sell.amount_invested.sum())
            self.cash.append(self.cash[-1] + to_sell.investment_return.sum())
            self.aum.append(self.invested[-1] + self.cash[-1])

            # Win and loss rate flag based on returns calculations

            self.portoflio = self.portfolio.drop([current_date])
            self._debug(f'Pnl: {pnl}')
            self._debug(f'Positions sold: {len(to_sell)}')
        else:
            self.cash.append(self.cash[-1])
            self.invested.append(self.invested[-1])
            self.aum.append(self.invested[-1] + self.cash[-1])

        self._debug(f'Cash:{self.cash[-1]} | Invested: {self.invested[-1]}')
        
    def History(self, full_data, lookback, current_date):
        '''Function to return a window of past data on a t-1 to t-n period. Only take into account values
        Where the exit_date < current date'''
        pass

    def _debug(self, msg):
        if self.debug == True:
            print(f'{msg}')

class OrtexBacktestEngine(core):
    def __init__(self, data: pd.DataFrame, starting_capital: int, sig_level:int, run_now = True, debug = True):
        core.__init__(self, starting_capital, debug)
        self.data = data
        self.debug = debug
        self.sig_level = sig_level
        self.run_now = run_now

        if self.run_now == True:
            self.run()

    def run(self):
        for date, _slice in self.data.groupby(level = 0):
            self._debug(date)

            # sort data by significance, and only keep those with greater than 80%
            to_trade = _slice.loc[_slice.significance > self.sig_level].sort_values('significance', ascending = False).head(1)

            # Trade 1% of the portfolio for the time being
            per_trade = self.aum[-1] * 0.01

            # track portfolio if we have open positions
            # we prioritise selling positions as opposed to buying them
            if len(self.portfolio)>0:
                self.TrackPortfolio(date)
            
            # enter trade by passing in stocks we wish to trade on as well as the amount invested
            amount_invested = self.EnterTrade(to_trade, per_trade)
            self.invested[-1] = self.invested[-1] + amount_invested
            self.cash[-1] = self.cash[-1]-amount_invested

            del _slice  # removing the variable from memory 

    def run_allocations(self):
        for date, _slice in self.data.groupby(level = 0):
            self._debug(date)

            # sort data by significance, and only keep those with greater than 80%
            to_trade = _slice.loc[_slice.significance > self.sig_level].sort_values('significance', ascending = False).head(1)

            # Trade amount based on a function of the significance as well as the required holding days
            # Prefernce for high significance and short holding days as quicker and more reliable returns
            # Thus, we want a decreasing function of these. 
            per_trade = self.calculate_trade(to_trade)
            # track portfolio if we have open positions
            # we prioritise selling positions as opposed to buying them
            if len(self.portfolio)>0:
                self.TrackPortfolio(date)
            
            # enter trade by passing in stocks we wish to trade on as well as the amount invested
            amount_invested = self.EnterTrade(to_trade, per_trade)
            self.invested[-1] = self.invested[-1] + amount_invested
            self.cash[-1] = self.cash[-1]-amount_invested

            del _slice  # removing the variable from memory 
    
    def calculate_trade(self, to_trade):
        '''Define required holding day buckets'''
        short_term = 10
        mid_term = 30
        long_term = 60
        pass

    def run_ML(self, lookback = 252):
        i = 0  #int to reference length of lookback window

        for date, _slice in self.data.groupby(level = 0):
            i+=1
            if i > lookback:
                history = self.History(lookback)
                
                # after returning clean history, group into buckets for significance, required holding days and returns
                # to start run regression on them
                # need some sort of "feedback mechanism" on trades, i.e if the trade "won" or "lost" assign some signficance
                # This is "reinforcement learning"

    def strategy_results(self):
        print(len(self.aum), len(self.cash), len(self.invested))
        res = pd.DataFrame(columns = ['AUM', 'CASH', 'INVESTED'] )
        index = sorted(list(set([x[0] for x in self.data.index])))
        res.CASH = self.cash
        res.INVESTED = self.invested
        res.AUM = self.aum
        res.index = index
        return res


    def kelly_crtierion(self, prob_of_win, b):
        '''We will use this in later iterations of the strategy to include ML models.
        In theory, once we have groups of returns against rec_holding_days and significance as a
        probability of a win (p) the formula;  p + (p-1)/b, b is amount gained in win. We can structure our bets
        according to this formula. Under conditional probaility we can say that b is the probability multiplied by the payoff
        of other similar grouped trades w.r.t significance and rec_holding_days. This probability would be 
        encapsulated within our "learning" part" under the current win-rate calculations for the period. 
        We can go one step further, and break up our significance into buckets to which we assign capital based on this'''
        pass

if __name__ == '__main__':
    import pandas as pd
    pd.set_option('mode.chained_assignment', None)  # to prevent copy warning as we know what we are doing :-)
    from engine import OrtexBacktestEngine

    df = pd.read_csv('../Pdata/data.csv', index_col = 0, parse_dates = True)
    df.reset_index(inplace = True)
    # remap the buy and sell to a binary output
    df.buy = df.buy.astype(int)
    df.signal_return = df.signal_return.astype(float)
    df_long = df.loc[df.buy == 1]
    df_long['exit_date'] = df_long['date'] + pd.to_timedelta(df_long.rec_holding_days, unit = 'd')
    df_long.set_index(['date', 'ticker'], inplace = True)

    bt = OrtexBacktestEngine(df_long, 100000)
    print(bt.run(80))
    print(bt.portfolio)
