import pandas as pd
class core():
    def __init__(self, starting_capital):
        self.starting_capital = starting_capital
        self.invested = []
        self.cash = []
        self.trades_won = 0
        self.trades_lost = 0
        self.invested.append(0) 
        self.cash.append(self.starting_capital)
        self.portfolio = pd.DataFrame()

    def EnterTrade(self, _slice, amt_to_trade):
        # take a given slice, allocate amount invested and store in self.portfolio
        # negate total amount of amt_to_trade 
        _slice.reset_index(inplace = True)
        _slice['amount_invested'] = amt_to_trade
        total_investment = _slice['amount_invested'].sum()

        _slice['investment_return'] = _slice['amount_invested'] * (1 + _slice['signal_return']/100)
        _slice.set_index('exit_date', inplace = True)

        self.portfolio = pd.concat([self.portfolio, _slice], axis = 0)
        self.cash.append(self.cash[-1] - total_investment ) #append new cash position
        self.invested.append(self.invested[-1] + total_investment)

    def TrackPortfolio(self, current_date):
        # apply a mask over those we wish to sell
        to_sell = self.portfolio.loc[current_date]
        # if the mask applied is not empty, trade out of those positions
        if not to_sell.empty:
            self._debug('to sell')
            returns = to_sell.investment_return.sum()
            self.invested.append(self.invested[-1] - returns)
            self.cash.append(returns)
            self.portfolio.drop(current_date)
        else:
            self._debug('continuation')
            self.cash.append(self.cash[-1])
            self.invested.append(self.invested[-1])

        self._debug(f'cash: {self.cash}')
        self._debug(f'invested: {self.invested}')
        
    def History(self, full_data, lookback, current_date):
        '''Function to return a window of past data on a t-1 to t-n period. Only take into account values
        Where the exit_date < current date'''
        pass

    def _debug(self, msg):
        print(f'{msg}')

class OrtexBacktestEngine(core):
    def __init__(self, data: pd.DataFrame, starting_capital):
        core.__init__(self, starting_capital)
        self.data = data

    def run(self, sig_level):

        for date, _slice in self.data.groupby(level = 0):
            self._debug(date)
            # sort data by significance, and only keep those with greater than 80%
            to_trade = _slice.loc[_slice.significance > sig_level].sort_values('significance', ascending = False)
            amt_to_trade = self.cash[-1] + self.invested[-1]

            # Trade 1% of the portfolio for the time being
            per_trade = amt_to_trade * 0.01

            if len(self.portfolio)>0:
                self._debug('has holdings')
                self.TrackPortfolio(date)
                
            self.EnterTrade(to_trade, per_trade)
            
            del _slice

        return self.strategy_results()
    
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

    def strategy_results():
        res = pd.DataFrame(columns = ['AUM', 'CASH', 'INVESTED'])
        res.CASH = self.cash
        res.INVESTED = self.invested
        res.AUM = res.CASH + res.INVESTED
        return res


    def kelly_crtierion(self, prob_of_win, b):
        '''We will use this in later iterations of the strategy to include ML models.
        In theory, once we have groups of returns against rec_holding_days and significance as a
        probability of a win (p) the formula;  p + (p-1)/b, b is amount gained in win. We can structure our bets
        according to this formula. Under conditional probaility we can say that b is the probability multiplied by the payoff
        of other similar grouped trades w.r.t significance and rec_holding_days'''
        pass

if __name__ == '__main__':
    pass
