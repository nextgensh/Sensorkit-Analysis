

import marimo

__generated_with = "0.13.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    import math
    import json
    return json, math


@app.cell
def _():
    # Install the sensorkit dependency so you can connect directly to the MDH source
    from sensorfabric.needle import Needle
    from sensorfabric.athena import athena
    return Needle, athena


@app.cell
def _(Needle, athena):
    # Create a new connection to MDH

    # Start by creating a new profile in .aws/credentials that connect to MDH.
    Needle(method='mdh', profileName='sensorkit-alacrity', offlineCache=True)

    # Create a SF Athena object that 
    mdh = athena(profile_name='sensorkit-alacrity', 
                 database='mdh_export_database_rk_652a14ae_digital_therapy_sensor_project_prod', 
                 s3_location='s3://pep-mdh-export-database-prod/execution/rk_652a14ae_digital_therapy_sensor_project', 
                 workgroup='mdh_export_database_external_prod',
                offlineCache=True) 
    return (mdh,)


@app.cell
def _(mo):
    mo.md(r"""The database table for sensor kit is named 'sensorkit'. Lets take a look at an example output from it.""")
    return


@app.cell
def _(mdh):
    mdh.execQuery('select * from sensorkit limit 10')
    return


@app.cell
def _(mo):
    mo.md(r"""Lets go ahead and filter it only by those who have completed the baseline survey.""")
    return


@app.cell
def _(mdh):
    def getParticipantsBaseline():
        query = """
            SELECT
              participantidentifier
            FROM
              segmentparticipants
            WHERE
              segmentname = 'Baseline Complete'
        """

        results = mdh.execQuery(query)

        return results
    return (getParticipantsBaseline,)


@app.cell
def _(getParticipantsBaseline):
    participants = getParticipantsBaseline()
    return (participants,)


@app.cell
def _(mo):
    mo.md(r"""Lets look at participants who have sensorkit data that has come in.""")
    return


@app.cell
def _(mdh):
    def SK_getParticipants():
        query = """
            select distinct(participantid)
                from sensorkit
        """

        result = mdh.execQuery(query)

        return result
    return (SK_getParticipants,)


@app.cell
def _(SK_getParticipants):
    sk_participants = SK_getParticipants()
    return (sk_participants,)


@app.cell
def _(math, mo, participants, sk_participants):
    mo.md(f"""There are a total of {sk_participants.shape[0]} with sensorkit data amongst {participants.shape[0]} total participants for a percentage of {math.ceil(sk_participants.shape[0]*100/participants.shape[0])}%""")
    return


@app.cell
def _(mo, sk_participants):
    p_dropdown = mo.ui.dropdown(sk_participants['participantid'].values)
    return (p_dropdown,)


@app.cell
def _(mo, p_dropdown):
    mo.md(f"""Pick a participant with sensorkit data - {p_dropdown}""")
    return


@app.cell
def _(mo, p_dropdown):
    selected_participant = p_dropdown.value
    mo.md(f'Participant Selected - {selected_participant}')
    return (selected_participant,)


@app.cell
def _(mdh, mo, selected_participant):
    q1 = f"""select sampletype, array_agg(distinct(devicetype)) devices
        from sensorkit where participantid='{selected_participant}' group by sampletype"""
    r1 = mdh.execQuery(q1)
    mo.ui.table(r1, selection=None)
    return (r1,)


@app.cell
def _(mo, r1):
    s_dropdown = mo.ui.dropdown(r1['sampletype'].values)
    return (s_dropdown,)


@app.cell
def _(s_dropdown):
    s_dropdown
    return


@app.cell
def _(mo):
    mo.md(r"""# Example Data Frame""")
    return


@app.cell
def _(mdh, p_dropdown, s_dropdown):
    q2 = f"""select * from sensorkit where sampletype = '{s_dropdown.value}' and participantid = '{p_dropdown.value}' limit 1"""
    r2 = mdh.execQuery(q2)
    r2
    return


@app.cell
def _(mo):
    mo.md(r"""# Understanding Sample Begin and End Times""")
    return


@app.cell
def _(mdh, p_dropdown, s_dropdown):
    q3 = f"""
        select participantid, samplequerybegin, sampletimestampend 
            from sensorkit
            where participantid = '{p_dropdown.value}'
            and sampletype = '{s_dropdown.value}'
            and devicetype = 'AppleWatch'
    """
    r3 = mdh.execQuery(q3, cached=True)
    r3
    return


@app.cell
def _(mo):
    mo.md(r"""Understanding the range of data we have for this sample type.""")
    return


@app.cell
def _(mdh, p_dropdown, s_dropdown):
    date_summary = mdh.execQuery(f"""
            select participantid, min(samplequerybegin) start, max(sampletimestampend) stop
            from sensorkit
            where participantid = '{p_dropdown.value}'
            and sampletype = '{s_dropdown.value}'
            and devicetype = 'AppleWatch'
            group by participantid
    """, cached=True)

    date_summary
    return (date_summary,)


@app.cell
def _(mdh, p_dropdown, s_dropdown):
    mdh.execQuery(f"""
            select samplequerybegin, count(*)
            from sensorkit
            where participantid = '{p_dropdown.value}'
            and sampletype = '{s_dropdown.value}'
            and devicetype = 'AppleWatch'
            group by samplequerybegin
            order by samplequerybegin
    """, cached=True)
    return


@app.cell
def _(mo):
    mo.md(r"""Looks like there is fixed number of values per window (samplequerybegin, sampletimestampend). So we can only roughly narrow it down to that interval and after that we are forced to read everything inside it.""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        # Sample Structure

        Each metric returns an array of samples. Here we look at an example of how the samples for each data type might look like
        """
    )
    return


@app.cell
def _(date_summary, mo):
    from datetime import datetime
    import datetime as DT

    dc = lambda x : datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f').date()
    cal = mo.ui.date_range(start=dc(date_summary['start'].array[0]), stop=dc(date_summary['stop'].array[0]))

    cal
    return DT, cal, datetime


@app.cell
def _(cal, mo):
    mo.md(f"""Date Range - {cal.value[0]} to {cal.value[1]}""")
    return


@app.cell
def _(cal, mdh, p_dropdown, s_dropdown):
    sample_data = mdh.execQuery(f"""
            select participantid, samples
            from sensorkit
            where participantid = '{p_dropdown.value}'
            and sampletype = '{s_dropdown.value}'
            and devicetype = 'AppleWatch' 
            and cast(samplequerybegin as date) >= date('{cal.value[0]}')
            and cast(sampletimestampend as date) <= date('{cal.value[1]}')
    """, cached=True)

    sample_data
    return (sample_data,)


@app.cell
def _(json, mo, sample_data):
    example = json.loads(sample_data['samples'].iloc[0])
    mo.json(example)
    return (example,)


@app.cell
def _(DT, datetime, example):
    print(datetime.fromtimestamp(example['timestamp']//1000, DT.UTC))
    return


@app.cell
def _(DT, datetime, json):
    import pandas as pd

    def tabulateHR(sample_data):

        for sample in sample_data['samples']:
            j = json.loads(sample)
            s = j['sample']
            c = s['confidence']
            hr = s['heartRate']
            t = j['timestamp'] + s['timestamp']
            dt = datetime.fromtimestamp((j['timestamp'] + s['timestamp']) // 1000, DT.UTC)

            print(dt, t, hr, c)
    return (tabulateHR,)


@app.cell
def _(s_dropdown, sample_data, tabulateHR):
    if s_dropdown.value == 'sensorkit-heart-rate':
        tabulateHR(sample_data)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
