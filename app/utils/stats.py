from io import BytesIO
from collections import defaultdict
from app import db
import base64
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import seaborn as sns


# Use matplotlib in non-interactive mode. Consider changing the backend
# if a different image format besides SVG is needed.
matplotlib.use('svg')
# Increase the bottom axis padding to prevent rotated tick marks from
# being truncated.
plt.rcParams['figure.subplot.bottom'] = 0.2
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['lines.marker'] = 'o'
plt.rcParams['axes.labelsize'] = 14


def get_transactions_total(transactions: list[dict]):
    """Compute the sum of the value of all the given transactions."""
    return sum(int(t['amount']) for t in transactions)


def get_totals_by_subcategories(transactions: list[dict],
                                n: int = None) -> list[tuple[str, int]]:
    """
    Compute totals by subcategory and return the top n subcategories.

    Transactions with no subcategory will be grouped under 'Uncategorized'.
    Sample output: [('Food', 100), ('Electricity', 40), ...]
    """
    if not transactions:
        return []
    totals = defaultdict(int)
    for t in transactions:
        # Transactions with no subcategory will be put under 'uncategorized'
        if not t.get('subcategory'):
            totals['Uncategorized'] += int(t['amount'])
        else:
            totals[t['subcategory']] += int(t['amount'])

    # Sort results by amount in descending order
    totals = list(totals.items())
    if n and n > 0:
        totals = totals[:n]
    return sorted(totals, key=lambda x: x[1], reverse=True)


def get_summary_stats(username, profile, from_=None, to=None):
    """Get transaction summaries for the given user profile."""
    incomes = db.get_transactions(username, profile, category='incomes',
                                  from_=from_, to=to)
    expenses = db.get_transactions(username, profile, category='expenses',
                                   from_=from_, to=to)

    top_incomes = get_totals_by_subcategories(incomes, n=5)
    top_expenses = get_totals_by_subcategories(expenses, n=5)
    total_income = get_transactions_total(incomes)
    total_expense = get_transactions_total(expenses)
    net_income = total_income - total_expense

    return {
        'top_incomes': top_incomes,
        'top_expenses': top_expenses,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_income': net_income
    }


def fig_to_base64(fig: plt.Figure, format='svg') -> str:
    f"""
    Encode a matplotlib Figure object to base64.

    :param fig: the Figure instance to be encoded
    :param format: the format of the encoded output. Options: 'svg', 'png'
    :return: an utf-8 encoded string representation of {fig}
    """
    buffer = BytesIO()
    fig.savefig(buffer, format=format)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    return encoded


def pie_chart(x: list[int | float], labels: list[str], title: str = '') -> str:
    """
    Plot pie chart with the given data.

    :param x: a list of numerical data to be plotted
    :param labels: a list of labels associated with the x values
    :param title: title to use for the chart
    :return: a base64-encoded pie chart of the data
    """
    if not x:
        return ''
    assert len(x) == len(labels), "'x' and 'labels' must have equal length"
    fig, ax = plt.subplots()
    ax.pie(x, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.set_title(title)
    return fig_to_base64(fig)


def get_summary_graphs(username, profile, top_incomes: list[tuple[str, int]],
                       top_expenses: list[tuple[str, int]],
                       from_=None, to=None) -> dict:
    """TODO: add docstring"""
    # Get all transactions for the period
    transactions = db.get_transactions(username, profile, from_=from_, to=to)
    if not transactions:
        return {}
    # Convert the transactions to a DataFrame
    df = pd.DataFrame(transactions)
    # Convert the 'time' column to a datetime column
    df['time'] = pd.to_datetime(df['time'])
    # Group transactions by month and aggregate by summing the amounts
    incomes = df[df['category'] == 'incomes']
    expenses = df[df['category'] == 'expenses']

    # Key Series objects for use in plotting
    incomes_monthly = aggregate_monthly(incomes)
    expenses_monthly = aggregate_monthly(expenses)
    if not incomes_monthly.empty:
        incomes_monthly = incomes_monthly.squeeze(axis=1)
    if not expenses_monthly.empty:
        expenses_monthly = expenses_monthly.squeeze(axis=1)
    # print("---------------before reindexing---------------")
    # print("---------------incomes_monthly-\n", incomes_monthly)
    # print("-------------expenses-monthly\n", expenses_monthly)
    incomes_monthly, expenses_monthly = reindex_series(incomes_monthly, expenses_monthly)
    net_monthly = incomes_monthly - expenses_monthly
    # print("---------------After reindexing---------------")
    # print("---------------incomes_monthly\n", incomes_monthly)
    # print("---------------expenses_monthly\n", expenses_monthly)
    # print("-----------------net\n", net_monthly)

    # Plot of monthly incomes and expenses
    monthly_income_expenses = monthly_cash_flows(
        incomes_monthly, expenses_monthly,
    )
    # Plot of monthly net income
    monthly_net_income = line_plot(net_monthly)
    # Plots of top incomes and expenses
    graph_pie_incomes = donut_chart(
        x=[i[1] for i in top_incomes],
        labels=[i[0] for i in top_incomes],
        # title='Top Income Sources'
    )
    graph_pie_expenses = donut_chart(
        x=[i[1] for i in top_expenses],
        labels=[i[0] for i in top_expenses],
        # title='Top Expenses'
    )

    return {
        'graph_pie_incomes': (
            f"Top Income Sources ({from_} to {to})",
            graph_pie_incomes
        ),
        'graph_pie_expenses': (
            f"Top Expenses ({from_} to {to})",
            graph_pie_expenses
        ),
        'graph_line_monthly_cash_flows': (
            'Trend: Total Monthly Incomes and Expenses',
            monthly_income_expenses
        ),
        'graph_line_monthly_net_income': (
            'Trend: Monthly Net Income',
            monthly_net_income
        ),
    }


def aggregate_monthly(transactions: pd.DataFrame):
    """Group transactions by month and aggregate by summing the amounts."""
    df = pd.DataFrame(transactions)
    # Convert to datetime if not already datetime.
    df['time'] = pd.to_datetime(df['time'])
    df_monthly = (
        df[['time', 'amount']]
        .groupby(pd.Grouper(key='time', freq='ME'))
        .sum()
    )
    return df_monthly


def reindex_series(s1: pd.Series, s2: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Make s1 and s2 conform to the same timeseries index.

    :param s1: a Series with a datetime index
    :param s2: a Series with a datetime index
    :return: a tuple containing new Series objects. The same input
        will be returned if both are empty
    """
    if s1.empty and s2.empty:
        return s1, s2
    if s1.empty and not s2.empty:
        new_index = pd.date_range(min(s2.index), max(s2.index), freq='ME')
        s1_new = pd.Series([], dtype=s2.dtype).reindex(new_index, fill_value=0)
        return s1_new, s2
    if not s1.empty and s2.empty:
        new_index = pd.date_range(min(s1.index), max(s1.index), freq='ME')
        s2_new = pd.Series([], dtype=s1.dtype).reindex(new_index, fill_value=0)
        return s1, s2_new

    # Both s1 and s2 are non-empty
    min_date = min([min(s1.index), min(s2.index)])
    max_date = max([max(s1.index), max(s2.index)])
    new_index = pd.date_range(min_date, max_date, freq='ME')
    s1_new = s1.reindex(new_index, fill_value=0)
    s2_new = s2.reindex(new_index, fill_value=0)
    return s1_new, s2_new


def monthly_cash_flows(incomes: pd.Series, expenses: pd.Series,
                       title: str = '') -> str:
    """
    Plot line graphs of monthly incomes and expenses on the same chart.

    :param incomes: timeseries of total monthly incomes
    :param expenses: timeseries of total monthly expenses
    :param title: the title to give to the graph
    :return: :return: a base64-encoded line chart of the data
    """
    if incomes.shape[0] < 2 or expenses.shape[0] < 2:
        # Do not plot if either Series does not have enough data.
        return ''
    fig, ax = plt.subplots()
    ax.plot(incomes, label='Total Monthly Income')
    ax.plot(expenses, label='Total Monthly Expenses')
    ax.set_title(title)
    ax.set_xlabel('Month')
    plt.xticks(rotation=60)
    ax.legend()
    return fig_to_base64(fig)


def line_plot(data: pd.Series, title: str = '') -> str:
    """
    Create a single line plot using the data.
    """
    if data.empty or data is None:
        return ''
    # Cannot draw line graph with only one point
    if data.shape[0] < 2:
        return ''
    fig, ax = plt.subplots()

    ax.plot(data)
    ax.set_title(title)
    ax.set_xlabel('Month')
    plt.xticks(rotation=60)
    return fig_to_base64(fig)


def bar_plot(x: list[int | float], labels: list[str], title: str = '') -> str:
    """
    Plot a bar plot with the given data.

    :param x: a list of numerical data to be plotted
    :param labels: a list of labels associated with the x values
    :param title: title to use for the chart
    :return: a base64-encoded bar chart of the data
    """
    if not x or len(x) < 2:
        return ''
    fig, ax = plt.subplots()
    ax.set_xlabel('Amount')
    ax.set_title(title)
    sns.barplot(x=x, y=labels, orient='h', ax=ax)
    return fig_to_base64(fig)


def donut_chart(x, labels, title='') -> str:
    if not x or len(x) < 2:
        return ''
    # Sample data
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(x, labels=None, autopct='%1.0f%%', startangle=90)

    # Draw circle in the center
    centre_circle = plt.Circle((0, 0), 0.7, color='black', fc='white', linewidth=0)
    ax.add_artist(centre_circle)
    # Equal aspect ratio ensures that pie is drawn as a circle
    plt.axis('equal')
    plt.legend(labels, loc='upper right',
               bbox_to_anchor=(1.3, 0.7)
    )
    # Adjust the position of `ax` within `fig` to leave room for the legend
    plt.subplots_adjust(left=0, right=0.7, top=1, bottom=0)
    ax.set_title(title)
    return fig_to_base64(fig)


def count_charts(charts: dict) -> int:
    """
    Return the number of charts.

    The function iterates over the dict and counts the number of values
    for which the base64 string representing the chart is not empty.
    """
    n = 0
    for chart in charts:
        if charts[chart][1]:
            n += 1
    return n
