import pymysql
import pandas as pd
from datetime import datetime

class DBUpdater:
    def __init__(self):
        self.conn = pymysql.connect(host='localhost', user='root', password='1234', db='INVESTAR', charset='utf8')

        with self.conn.cursor() as curs:
            sql = """
            CREATE TABle IF NOT EXISTS company_info(
                code VARCHAR(20),
                company VARCHAR(40),
                last_update DATE,
                PRIMARY KEY(code))
            """
            curs.execute(sql)
            sql = """
            CREATE TABLE IF NOT EXISTS daily_price(
                code VARCHAR(20),
                date DATE,
                open BIGINT,
                high BIGINT,
                low BIGINT,
                close BIGINT,
                diff BIGINT,
                volume BIGINT,
                PRIMARY KEY(CODE, DATE))
            """

            curs.execute(sql)
        self.conn.commit()

        self.codes = dict()
        self.update_comp_info()

        def __del__(self):
            self.conn.close()

    def read_krx_code(self):
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        krx = pd.read_html(url, encoding='cp949', header=0)[0]
        krx = krx[['종목코드', '회사명']]
        krx = krx.rename(columns={'종목코드': 'code', '회사명': 'company'})
        krx.code = krx.code.map('{:06d}'.format)

        return krx

    def update_comp_info(self):
        #종목코드를 company_info 테이블에 업데이트한 후 딕셔너리에 저장
        sql = "SELECT * FROM company_info"
        df = pd.read_sql(sql, self.conn)
        for idx in range(len(df)):
            self.codes[df['code'].values[idx]]=df['company'].values[idx]

        with self.conn.cursor() as curs:
            sql = "SELECT max(last_update) FROM company_info"
            curs.execute(sql)
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d')

            if rs[0] is None or rs[0].strftime('%Y-%m-%d') < today:
                krx = self.read_krx_code()
                for idx in range(len(krx)):
                    code = krx.code.values[idx]
                    company = krx.company.values[idx]
                    sql = f"REPLACE INTO company_info (code, company, last_update) VALUES ('{code}', '{company}', '{today}')"
                    curs.execute(sql)
                    self.codes[code] = company
                    tmnow = datetime.now().strftime("%Y-%m-%d %H:%M")
                    print(f"[{tmnow}] {idx:05d} REPLACE INTO company_info VALUES ({code}, {company}, {today})")
                self.conn.commit()
                print('')

if __name__ == '__main__':
    dbu = DBUpdater()
    dbu.update_comp_info()