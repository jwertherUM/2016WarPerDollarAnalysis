from numpy import double
import requests
from bs4 import BeautifulSoup
import sqlite3
from pybaseball import playerid_lookup
from pybaseball import statcast_batter
from pybaseball import batting_stats
from pybaseball import pitching_stats

def gather_data(url='https://questionnaire-148920.appspot.com/swe/data.html'):
    data = requests.get(url)
    soup = BeautifulSoup(data.content, 'html.parser')
    rows = soup.find_all('tr')
    
    players = []
    for row in rows:
        sal = row.find('td', class_='player-salary').get_text()
        if (sal == '' or 
            sal == 'no salary data'):
            continue

        newSal = []
        for s in sal:
            if s.isdigit():
                newSal.append(s)
        
        sal = [str(integer) for integer in newSal]
        sal = "".join(sal)
        
        player = {
            "name": row.find('td', class_='player-name').get_text(),
            "salary": sal,
            "year": row.find('td', class_= 'player-year').get_text()
        }
        players.append(player)
    
    return players

def sql_analysis():
    connection = sqlite3.connect('data.db')
    cur = connection.cursor()

    cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='players' ''')
    if cur.fetchone()[0] == 1 :
        cur.execute("DROP TABLE players")
        connection.commit()
    
    cur.execute('''CREATE TABLE players 
                (name text, salary real, year real)''')
    connection.commit()
    
    
    data = gather_data()
    for datum in data:
        cur.execute("INSERT INTO players VALUES(?,?,?)", (datum['name'], int(datum['salary']), datum['year']))
        connection.commit()
    
    cur.execute(''' SELECT AVG(salary) FROM(
                    SELECT salary
                    FROM players
                    ORDER BY salary DESC
                    LIMIT 125)''')
    out = cur.fetchone()[0]

    cur.execute('''SELECT *
                    FROM players
                    ORDER BY salary DESC
                    LIMIT 125''')
    players = cur.fetchall()
    print()
    print("------------------------------------------------------------------")
    print("QUALIFYING OFFER: $" + str(out))
    
    bstats = batting_stats(2016)
    pstats = pitching_stats(2016)
    batters = []
    pitchers = []
    warSalary = []

    for p in players:
        n = p[0].split()
        last = n[0]
        last = last[:-1]
        first = n[1]

        qtext = "Name == '"+ first +" "+ last+"'"
        q = bstats.query(qtext)
        q2 = pstats.query(qtext)
        if q2.empty == False:
            pitchers.append(q2)
            warSalary.append([double(str(q2['WAR']).split()[1])/double(p[1]), first+" "+last])
        elif q.empty == False:
            batters.append(q)
            warSalary.append([double(str(q['WAR']).split()[1])/double(p[1]), first+" "+last])
    print()
    print("BREAKDOWN OF TOP 125 SALARY PLAYERS WITH AVAILABLE DATA")
    print("*PLAYERS WITH UNAVAILABLE DATA OMITTED*")
    print()
    print("-------------------------POSITION PLAYERS-----------------------------")
    print(("NAME").ljust(25) + ("AVG").ljust(7) + (("OBP")).ljust(7) + (("SLG").ljust(7)) + (("WAR").ljust(7)) )
    for b in batters:
        print((str(b['Name']).split()[1] +" "+str(b['Name']).split()[2]).ljust(25) + 
                (str(b['AVG']).split()[1]).ljust(7) +
                (str(b['OBP']).split()[1]).ljust(7) +
                (str(b['SLG']).split()[1]).ljust(7) +
                (str(b['WAR']).split()[1]).ljust(7)
                )
    print()
    print("----------------------------------PITCHERS----------------------------------")
    print()
    print(("NAME").ljust(26) + ("ERA").ljust(7) + (("WHIP")).ljust(7) + (("WAR").ljust(7)) + (("W/L").ljust(7)) )
    for p in pitchers:
        print((str(p['Name']).split()[1] +" "+str(p['Name']).split()[2]).ljust(25) + " " + 
                (str(p['ERA']).split()[1]).ljust(7) +
                (str(p['WHIP']).split()[1]).ljust(7) +
                (str(p['WAR']).split()[1]).ljust(7) +
                (str(p['W']).split()[1] + "-" + str(p['L']).split()[1]).ljust(7))
    print()
    print("----------------------------------VALUE PLAYS----------------------------------")
    print("*TOP 10 PLAYERS BY WAR/SALARY*")
    print()
    warSalary = sorted(warSalary, reverse=True)
    z = 0
    for w in warSalary:
        print(str(z + 1) + ". " + str(w[1]))
        z += 1
        if z == 10:
            break



sql_analysis()
print()