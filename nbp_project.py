import requests
from flask import (Flask, url_for, render_template, request, session, redirect)
from datetime import datetime
import pygal
from json2html import *
from flask_session import Session

DEFAULT_TEXT = 'Wybierz walutę'


def create_app():
    app = Flask(__name__)
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)

    return app


app = create_app()


@app.route('/', methods=['GET', 'POST'])
def root():
    session.clear()
    start = ''
    stop = ''

    if request.method == 'POST' and request.form.get('button') == 'True':

        session['start'] = request.form.get('start_date')
        session['stop'] = request.form.get('stop_date')

        start = datetime.strptime(session['start'], "%Y-%m-%d")
        stop = datetime.strptime(session['stop'], "%Y-%m-%d")

        if start <= stop:
            err = False
            return render_template('nbp_start_page.html',
                                   start=session['start'],
                                   stop=session['stop'],
                                   err=err,
                                   button=True)
        else:
            err = True
            return render_template('nbp_start_page.html',
                                   start=session['start'],
                                   stop=session['stop'],
                                   err=err)

    elif request.method == 'POST' and request.form.get('button1') == 'True' and len(start) * len(stop) != 0:

        return redirect(url_for("download"))

    return render_template('nbp_start_page.html')


@app.route('/download', methods=['GET', 'POST'])
def download():
    start = ''
    stop = ''

    if 'start' and 'stop' in session:
        start = session['start']
        stop = session['stop']
        print(type(start), stop)
        if start == stop:
            url = f'https://api.nbp.pl/api/exchangerates/tables/A/' + start + '/?format=json'
        else:
            url = f'https://api.nbp.pl/api/exchangerates/tables/A/' + start + '/' + stop + '/?format=json'
        print("url",url)
        try:

            uResponse = requests.get(url)
            print(uResponse)
            Jresponse = uResponse.text

            with open('file.json', 'w') as file:
                file.writelines(Jresponse)

        except requests.ConnectionError:

            return "Blad polaczenia"

        try:
            data_json = uResponse.json()
        except ValueError as e:
            return "Brak danych w dniu " \
                   + str(start) \
                   + '<form class="pure_form" method="POST" action="/"><button type="submit" ' \
                     'name="button1" value="True">Powrót</button><br></form>'

        rates = data_json[0]['rates']

        currency = [i['currency'] for i in rates]
        currency.append(DEFAULT_TEXT)

        html_data = json2html.convert(json=Jresponse)  # all table converted to html

        graph = None
        all_values = [None, None, None]
        units = [DEFAULT_TEXT] * 3
        date = ''

        if request.method == 'POST' and request.form.get('button2') == 'True':
            all_values, units, date = explore_data(units, data_json, all_values)

            graph = draw_graph(all_values, date, units)

        elif request.method == 'POST' and request.form.get('button3') == 'True':
            return html_data \
                   + '<form class="pure_form" method="POST" action="/download"><button type="submit" ' \
                     'name="button5" value="True">Powrot</button><br></form>'

        elif request.method == 'POST' and request.form.get('button4') == 'True':
            units = reset_units()

        return render_template('download.html',
                               start=start,
                               stop=stop,
                               currency=currency,
                               last_value=units,
                               html_data=html_data,
                               graph=graph)

    return render_template('download.html',
                           start=start,
                           stop=stop)


def reset_units():
    units = [DEFAULT_TEXT] * 3
    return units


def get_currency_data(data, unit):
    date = [i['effectiveDate'] for i in data]
    values = [data[i]['rates'][j]['mid']
              for i in range(len(data))
              for j in range(len(data[0]['rates']))
              if data[i]['rates'][j]['currency'] == unit
              ]

    return date, values


def draw_graph(values, date, units):
    date_chart = pygal.Line(x_label_rotation=25,
                            legend_box_size=18)
    date_chart.x_labels = date

    for i in range(len(units)):

        if units[i] != DEFAULT_TEXT:
            # date_chart.title = 'Wykres walut w okresie od {} do {}'.format(date[0], date[-1])
            date_chart.add(str(units[i]), values[i])

    date_chart.render()
    graph = date_chart.render_data_uri()

    return graph


def explore_data(units, data_json, all_values):
    selects = ['selection', 'selection1', 'selection2']

    for i in range(3):
        unit = request.form.get(selects[i])
        # print(unit)
        units[i] = unit
        if unit != DEFAULT_TEXT:
            date, values = get_currency_data(data_json, unit)

            all_values[i] = values
    return all_values, units, date


if __name__ == '__main__':

    app.run(debug=True, port=8000, host='127.0.0.1')
