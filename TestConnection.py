# Install the sensorkit dependency so you can connect directly to the MDH source
from sensorfabric.needle import Needle
from sensorfabric.athena import athena

# Create a new connection to MDH

# Start by creating a new profile in .aws/credentials that connect to MDH.
Needle(method='mdh', profileName='sensorkit-alacrity', offlineCache=True)

# Create a SF Athena object that 
mdh = athena(profile_name='sensorkit-alacrity', 
             database='mdh_export_database_rk_652a14ae_digital_therapy_sensor_project_prod', 
             s3_location='s3://pep-mdh-export-database-prod/execution/rk_652a14ae_digital_therapy_sensor_project', 
             workgroup='mdh_export_database_external_prod',
            offlineCache=True)

frame = mdh.execQuery('select * from sensorkit limit 11')

print(frame)
