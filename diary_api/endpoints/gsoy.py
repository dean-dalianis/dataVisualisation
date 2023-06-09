from flask import request
from flask_restx import Api, Resource, fields
from influx.gsoy import fetch_data
from logging_config import logger


def initialize_routes(api: Api):
    gsoy_namespace = api.namespace('diary/gsoy', description='Basic climate data for countries')

    gsoy_measurement = api.model('gsoy', {
        'measurement': fields.String(required=True, description='Measurement name'),
        'country_iso': fields.String(required=True, description='Country ISO'),
        'country_name': fields.String(required=True, description='Country name'),
        'value': fields.Float(required=True, description='Measurement value'),
        'time': fields.DateTime(required=True, description='Timestamp', dt_format='iso8601'),
    })

    @gsoy_namespace.route('/data')
    class ClimateData(Resource):
        @gsoy_namespace.doc('fetch_climate_data',
                            params={'country_iso': {'description': 'A country iso', 'type': 'string', 'default': 'US'},
                                    'measurement': {'description': 'A measurement name', 'type': 'string',
                                                    'default': 'Average_Temperature'},
                                    'date': {'description': 'A specific date (YYYY-MM-DD)', 'type': 'string',
                                             'default': None},
                                    'start_date': {'description': 'Start date of a range (YYYY-MM-DD)',
                                                   'type': 'string', 'default': '2016-01-01'},
                                    'end_date': {'description': 'End date of a range (YYYY-MM-DD)', 'type': 'string',
                                                 'default': '2022-12-31'}},
                            responses={200: 'Climate data matching the specified conditions.',
                                       404: 'No data found for the specified conditions.'},
                            return_model=gsoy_measurement)
        @gsoy_namespace.marshal_list_with(gsoy_measurement)
        def get(self):
            """
            Fetch climate data based on specified conditions
            """
            country_iso = request.args.get('country_iso')
            measurement = request.args.get('measurement')
            date = request.args.get('date')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            if date and (start_date or end_date):
                return {"message": "You cannot set both 'date' and 'start_date'/'end_date' parameters."}, 400

            logger.info(
                f'Fetching climate data for country iso: {country_iso}, measurement: {measurement}, date: {date}, '
                f'start date: {start_date}, end date: {end_date}.')
            data = fetch_data(country_iso, measurement, date, start_date, end_date)
            logger.info(f'Fetched {len(data) if data is not None else "0"} climate data records.')

            if data:
                return data, 200
            else:
                return {
                           "message": "No climate data found for the specified conditions. Are you sure you are using the correct API endpoint?"}, 404
