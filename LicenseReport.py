#!/usr/bin/python



import psycopg2
import traceback
from configparser import ConfigParser
# from config import config
import pandas as pd
import argparse
import sys


parser = argparse.ArgumentParser("Show Overall License Risks")
parser.add_argument("-project_name",help="Limit output to single project")
parser.add_argument("-url",help="Provide the url for your instance (used to generate urls to link back to BD")
parser.add_argument("-d","--debug", action="store_true",help="Enable debug output")
parser.add_argument("-f","--file",help="Output file name")

args=parser.parse_args()

if not args.file:
    print("Please supply a file name ")
    parser.print_help()
    sys.exit(1)

def config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db

def connect(args):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)

        # create a cursor
        cur = conn.cursor()
        base_select='SELECT p.project_name,pv.version_name,c.component_name,c.component_version_name,'+ \
                    'c.license_high_count,c.license_medium_count,c.license_low_count,' + \
                    'cl.license_display,p.project_id,pv.version_id FROM project AS p '+ \
                    'INNER JOIN project_version AS pv ON p.project_id=pv.project_id ' + \
                    'INNER JOIN component AS c ON c.project_version_id=pv.version_id '  + \
                    'INNER JOIN component_license AS cl ON cl.component_table_id =  c.id '

        second_select='SELECT p.project_name AS "Parent Name",pv.version_name AS "Parent Version",p2.project_name,'+ \
                    'pv2.version_name,c2.component_name,c2.component_version_name,c2.license_high_count,c2.license_medium_count,c2.license_low_count,cl.license_display,p2.project_id,pv2.version_id FROM project AS p ' + \
                    'INNER JOIN project_version AS pv ON p.project_id=pv.project_id ' + \
                    'INNER JOIN component AS c ON c.project_version_id=pv.version_id ' + \
                    'INNER JOIN project AS p2 ON c.component_id=p2.project_id ' + \
                    'INNER JOIN project_version AS pv2 ON p2.project_id=pv2.project_id ' + \
                    'INNER JOIN component AS c2 ON c2.project_version_id=pv2.version_id ' + \
                    'INNER JOIN component_license AS cl ON cl.component_table_id =  c2.id;'


        if args.project_name:
            base_select=base_select + " AND p.project_name='"+args.project_name+"' "

        try:
            base_select=base_select + ";"
            print("Executing query 1")
            cur.execute(base_select)
            # display the PostgreSQL database server version
            res = cur.fetchall()

            df = pd.DataFrame(res, columns=("Project Name", "Project Version Name", "Component Name", "Component Version", "License High Count", "License Medium Count", "License Low Count", "License Info", "Project Id", "Version Id"))


            df.insert(0, 'Parent Version', '')
            df.insert(0, 'Parent Name', '')
            df['Parent Name']=df['Project Name']
            df['Parent Version'] = df['Project Version Name']

            print("Executing query 2")
            cur.execute(second_select)
            res = cur.fetchall()
            df2 = pd.DataFrame(res, columns=("Parent Name","Parent Version",
            "Project Name", "Project Version Name", "Component Name", "Component Version", "License High Count", "License Medium Count", "License Low Count", "License Info", "Project Id",
            "Version Id"))

            df = df.append(df2)
            df = df.sort_values("Parent Name")


            def license_risk(row):
                if row['License High Count']>0:
                    return "High"
                elif row['License Medium Count']>0:
                    return "Medium"
                elif row['License Low Count'] > 0:
                    return "Low"

                return "OK"

            df.insert(6,'License Risk','')
            df['License Risk']=df.apply(license_risk,  axis=1)
            del df['License High Count']
            del df['License Medium Count']
            del df['License Low Count']



            def ambiguous():
                return lambda row: "True" if " AND " in row['License Info'] or " OR " in row['License Info' ] else "False"
            df['Ambiguous License']= df.apply(ambiguous(), axis=1)

            if args.url:
                def generate_url():
                    return lambda row: args.url+"/api/projects/"+row['Project Id']+"/versions/"+row['Version Id']+"/components?sort=projectName%20ASC&offset=0&limit=100&filter=bomInclusion%3Afalse&filter=licenseRisk%3Ahigh"
                df['Version Url'] = df.apply(generate_url(), axis=1)
                del df['Project Id']
                del df['Version Id']


        except Exception as e:
            print(traceback.format_exc())
            print("Caught exception:"+str(e))

        with open(args.file,"w") as f:
            df.to_csv(f,index=False,line_terminator='\r')

    # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

if __name__ == '__main__':
    connect(args)