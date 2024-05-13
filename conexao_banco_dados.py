# conexaoBancoDados.py
import cx_Oracle

def get_connection():
    return cx_Oracle.connect('VIASOFT/VIASOFT@viasoft-scan.vms.com.br:1521/plan')