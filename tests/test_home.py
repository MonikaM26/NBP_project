import pytest
import nbp_project as nbp
import responses, requests
import pytest
from pytest_mock import mocker
import flask


@pytest.fixture()
def app():
    yield nbp.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def read_():
    data = [
        {"table": "A",
         "no": "086/A/NBP/2023",
         "effectiveDate": "2023-01-02",
         "rates":
             [{"currency": "bat (Tajlandia)", "code": "THB", "mid": 0.1233},
              {"currency": "dolar amerykański", "code": "USD", "mid": 4.1612},
              {"currency": "dolar australijski", "code": "AUD", "mid": 2.8000},
              {"currency": "dolar Hongkongu", "code": "HKD", "mid": 0.5301},
              ]}]
    return data


def test_root(app, client):
    response = client.get('/')
    statuscode = response.status_code

    assert statuscode == 200
    assert b"<title>Analizator walut NBP </title>"


def test_root_date(app, client):
    response = client.post("/", data={"button": "True",
                                      "start_date": '2023-01-01',
                                      "stop_date": "2023-02-02"}
                           )
    # print(response.get_data('button'))
    assert b'2023-01-01' in response.data
    assert b'2023-02-02' in response.data

    response = client.post("/", data={"button": "True",
                                      "start_date": '2023-03-01',
                                      "stop_date": "2023-01-01"}
                           )
    # print(response.get_data('button'))
    assert b'Bledny przedzial czasowy!' in response.data


def test_brak_danych(client):
    out = client.post("/", data={"button": "True",
                                 "start_date": '2023-05-06',
                                 "stop_date": "2023-05-06"}
                      )

    assert b'2023-05-06' in out.data
    values = client.post("/download")
    assert b'Brak danych w dniu 2023-05-06' in values.data

    client.post("/", data={"button": "True",
                           "start_date": '2023-01-01',
                           "stop_date": "2023-02-02"}
                )

    response = client.post('/download')
    assert b'<option value="bat (Tajlandia)">bat (Tajlandia)</option>' in response.data


@responses.activate
def test_download(app, client, read_):
    url = 'https://api.nbp.pl/api/exchangerates/tables/A/2023-01-02/2023-01-03/?format=json'

    responses.add(
        responses.GET,
        url=url,
        json=read_,
        status=200
    )

    client.post("/", data={"button": "True",
                           "start_date": '2023-01-02',
                           "stop_date": '2023-01-03'})

    response = client.post('/download')
    assert b'<option value="dolar australijski">dolar australijski</option>' \
           in response.get_data()
    assert response.status_code == 200


@responses.activate
def test_download_ConnectionError(app, client):
    #   testing ConnectionError
    url = 'https://api.nbp.pl/api/exchangerates/tables/A'
    responses.add(
        responses.GET,
        url=url,
        json={}
    )
    client.post("/", data={"button": "True",
                           "start_date": '2023-01-02',
                           "stop_date": '2023-01-03'})

    response = client.post('/download')
    assert b'Blad polaczenia' in response.get_data()


@responses.activate
def test_graph(app, client, read_):
    url = 'https://api.nbp.pl/api/exchangerates/tables/A/2023-01-02/2023-01-03/?format=json'

    responses.add(
        responses.GET,
        url=url,
        json=read_,
        status=200
    )
    client.post("/", data={"button": "True",
                           "start_date": '2023-01-02',
                           "stop_date": '2023-01-03'})

    client.post('/download')
    out = client.post('/download', data={'selection': 'dolar amerykański',
                                         'button2': 'True'})
    assert b'image/svg+xml' in out.get_data()

    out = client.post('/download', data={'selection1': 'dolar amerykański',
                                         'button2': 'True'})
    assert b'image/svg+xml' in out.get_data()

    out = client.post('/download', data={'selection2': 'dolar amerykański',
                                         'button2': 'True'})
    assert b'image/svg+xml' in out.get_data()

    out = client.post('/download', data={'selection': 'dolar australijski',
                                         'selection1': 'dolar amerykański',
                                         'button2': 'True'})
    assert b'image/svg+xml' in out.get_data()

    out = client.post('/download', data={'selection': 'dolar Hongkongu',
                                         'selection1': 'dolar australijski',
                                         'selection2': 'dolar amerykański',
                                         'button2': 'True'})
    assert b'image/svg+xml' in out.get_data()
    # print(out.get_data().decode('utf-8','ignore'))


@responses.activate
def test_download_buttons(client, read_):
    url = 'https://api.nbp.pl/api/exchangerates/tables/A/2023-01-02/2023-01-03/?format=json'

    responses.add(
        responses.GET,
        url=url,
        json=read_,
        status=200
    )
    client.post("/", data={"button": "True",
                           "start_date": '2023-01-02',
                           "stop_date": '2023-01-03'})

    client.post('/download')
    out = client.post('/download', data={'button3': 'True'})
    assert b'table' in out.data
    assert b'Powrot' in out.data

    out = client.post('/download', data={'button5': 'True'})
    assert b'<title>Pobranie danych</title>' in out.data

    out = client.post('/download', data={'selection': 'dolar australijski'})


def test_reset_units():
    assert [nbp.DEFAULT_TEXT, nbp.DEFAULT_TEXT, nbp.DEFAULT_TEXT] == nbp.reset_units()
    assert isinstance(nbp.reset_units(), list)
    assert isinstance(nbp.reset_units()[0], str)


def test_get_currency_data(read_):
    date, values = nbp.get_currency_data(read_, 'dolar australijski')

    assert '2023-01-02' in date
    assert 2.8000 in values


def test_draw_graph():
    units = [nbp.DEFAULT_TEXT] * 3
    values = [11, 12, 11, 12]
    date = ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']
    out = nbp.draw_graph(values, date, units)
    assert isinstance(out, str)
    assert 'image/svg+xml' in out



