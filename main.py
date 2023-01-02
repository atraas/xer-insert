import pandas as pd
import time

start = time.time()
INPUT_FILE = '23Q1-WC-P6-15.2.xer'
DB_NAME = 'example_db'
TABLE_NAME = 'example_table'
TABLES = ['TASK', 'TASKPROC']


def extract_fields(lines, index):
    return [field.strip() for field in lines[index + 1].split('\t')[1:]]


def extract_split_records(lines, index: int):
    temp_index = index + 2
    while True:
        next_line = lines[temp_index]
        if not next_line.startswith('%R'):
            raw_records = [raw_record for raw_record in lines[index + 2:temp_index]]
            split_records = [split_record.split('\t') for split_record in raw_records]
            break
        temp_index += 1
    return split_records


def main():
    print(f'Reading file: {INPUT_FILE}')
    with open(INPUT_FILE) as handle:
        lines = handle.readlines()
        lines = lines[1:]

    for index in range(len(lines)):
        line = lines[index]
        if line.startswith('%T'):
            table = line.split('\t')[1].strip()
            if table == 'TASK':
                task_fields = extract_fields(lines, index)
                tasks_split_records = extract_split_records(lines, index)
                tasks_records = [tasks_record[1:-1] for tasks_record in tasks_split_records]
                task = pd.DataFrame.from_records(tasks_records, columns=task_fields)
            elif table == 'TASKPROC':
                taskproc_fields = extract_fields(lines, index)
                taskproc_split_records = extract_split_records(lines, index)
                taskproc_records = [taskproc_record[1:] for taskproc_record in taskproc_split_records]
                taskproc = pd.DataFrame.from_records(taskproc_records, columns=taskproc_fields)

    try:
        joined_df = pd.merge(taskproc[['task_id', 'proc_name', 'proc_wt']], task[['task_id', 'task_code']])
        query = f"INSERT INTO {DB_NAME}.{TABLE_NAME} (task_id, proc_name, proc_wt, task_code) VALUES %s;"
        value_list = []
        for index, row in joined_df.iterrows():
            proc_name = row['proc_name'].replace("'", "").replace('"', "").replace("", "")
            value_list.append(f"('{row['task_id']}', '{proc_name}', '{row['proc_wt']}', '{row['task_code']}')")
        query = query % ",".join(value_list)
        with open('insert_xer.sql', 'wt') as handle:
            handle.write(query)

        end = time.time()
        print("Written insert query to insert_xer.sql")
        print(f"Finished in {round(end - start, 3)} seconds")
    except NameError:
        print("Table TASKPROC or TASK not found or not correctly parsed")


if __name__ == '__main__':
    main()
