import json
import os
import boto3
import time

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])

def lambda_handler(event, context):
    try:
        # Extraer los datos del evento
        device_id = event['deviceId']
        temperatura = event['temperature']
        timestamp = event['timestamp']  # Timestamp recibido en el evento
        timestamp_number = int(time.mktime(time.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")))

        # Insertar los datos en la tabla DynamoDB
        response = table.put_item(
            Item={
                'deviceId': device_id,
                'timestamp': timestamp_number,  # Guardar el timestamp recibido
                'temperature': temperatura
            }
        )

        # Devolver respuesta de éxito
        return {
            'statusCode': 200,
            'body': json.dumps('Datos insertados correctamente')
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps('Error al insertar los datos')
        }
