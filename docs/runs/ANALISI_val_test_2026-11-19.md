# Analisi: perché validazione e test non concordano su rel-f1 (2026-11-19)

Confronto **solo sui dati** degli split di validazione (timestamp marzo 2005 – marzo 2008) e di test (marzo 2010 – marzo 2013)
di `driver-top3` e `driver-dnf`: nessun modello, nessuna GPU. Usata per la slide "two eras of F1" della presentazione.

Comando (nodo faretra, immagine `arc-relbench`, dalla root del repo):

```bash
docker run --rm --init --memory=8g -e HOME=/tmp -e ARC_NO_LLM=1 \
  -v "$PWD":/app -v "$PWD/docker-entrypoint.sh":/usr/local/bin/docker-entrypoint.sh:ro \
  arc-relbench:latest bash -c 'cd /app && python3 rb_task/tools/val_test_analysis.py --tasks driver-top3,driver-dnf'
```

Sezioni: 1 dimensioni degli split; 2 piloti in comune; 3 piloti e squadre dei positivi; 3b i protagonisti di uno split
nell'altro; 4 AUROC di regole semplici calcolate solo dal passato (anche per anno); 5 come cambia la Formula 1 per stagione.

Fatti principali (driver-top3): i 119 positivi di validazione vengono da 16 piloti (Alonso, Räikkönen, Massa = 48%; Ferrari,
McLaren, Renault), i 128 del test da 14 (Vettel, Hamilton, Webber = 60%; Red Bull 41%); Vettel e Webber hanno 52 positivi nel
test e 3 in validazione; 21 piloti su 42 sono in entrambi gli split. La regola "quota di top 3 del pilota nei 365 giorni
precedenti" dà AUROC 0,866 in validazione e 0,903 nel test (tutti gli esempi): il test non è più difficile, è diverso.
Le regole delle qualifiche cambiano tra i due periodi (2005–2009 con la benzina di gara, dal 2010 rifornimento vietato),
fonti: formula1.com, "Deciding the grid: a history of F1 qualifying formats"; Wikipedia, "2010 Formula One World Championship".

## Output

```text
Loading Database object from /opt/cache/relbench/rel-f1/db...
Done in 0.03 seconds.
val_timestamp 2005-01-01   test_timestamp 2010-01-01
qualifying rows 9,815 (1994-03-26 .. 2023-07-29), results rows 26,080

====================================================================================================
driver-top3  (target 'qualifying', data source {'db': 'download', 'task': 'download', 'from_cache': True})
====================================================================================================
1. Size of the splits
split  examples  timestamps      first       last  positives  pos_rate  drivers  drivers_with_a_positive  examples_per_driver
train      1353          59 1994-02-28 2004-10-03        231     0.171       92                       23   14.7
  val       588          27 2005-03-02 2008-03-16        119     0.202       42                       16   14.0
 test       726          30 2010-03-02 2013-03-16        128     0.176       42                       14   17.3

2. Which drivers: overlap between the splits
drivers in val 42, in test 42, in both 21
test examples whose driver is also in val: 61.0%; test positives whose driver is also in val: 93.8%
val positives whose driver is also in test: 88.2%
test drivers never seen in train or val: 21 (39.0% of the test examples)

3. Who the positives are (top-3 qualifying)
[val] 119 positives from 16 drivers; top 3 drivers 48%, top 5 66%
   drivers: Fernando Alonso 22, Kimi Räikkönen 20, Felipe Massa 15, Michael Schumacher 11, Giancarlo Fisichella 10, Lewis Hamilton 9, Jarno Trulli 6, Jenson Button 6
   teams:   Ferrari 35, McLaren 32, Renault 24, Toyota 8, BMW Sauber 6, Williams 5  (team of the driver's next qualifying)
[test] 128 positives from 14 drivers; top 3 drivers 60%, top 5 81%
   drivers: Sebastian Vettel 27, Lewis Hamilton 25, Mark Webber 25, Fernando Alonso 14, Jenson Button 13, Felipe Massa 6, Nico Rosberg 4, Pastor Maldonado 4
   teams:   Red Bull 52, McLaren 37, Ferrari 20, Mercedes 8, Williams 5, Lotus F1 3  (team of the driver's next qualifying)

3b. The 6 drivers with most positives in each split, seen in the other split (examples / positives)
   top of test: Sebastian Vettel 27 in test -> 7/0 in val; Lewis Hamilton 25 in test -> 11/9 in val; Mark Webber 25 in test -> 27/3 in val; Fernando Alonso 14 in test -> 27/22 in val; Jenson Button 13 in test -> 27/6 in val; Felipe Massa 6 in test -> 27/15 in val
   top of val: Fernando Alonso 22 in val -> 30/14 in test; Kimi Räikkönen 20 in val -> 11/1 in test; Felipe Massa 15 in val -> 30/6 in test; Michael Schumacher 11 in val -> 29/3 in test; Giancarlo Fisichella 10 in val -> 0/0 in test; Lewis Hamilton 9 in val -> 30/25 in test

4. How predictable each split is with simple rules (AUROC; computed only from data before each timestamp)
   rate, 365 d: share of the driver's (or of his last team's) sessions in the 365 days before the timestamp
   that ended in top-3 qualifying; last qualifying position: lower is better
split                     train    val   test
rule                                         
driver top-3 rate, 365 d  0.866  0.865  0.906
last qualifying position  0.884  0.841  0.900
team top-3 rate, 365 d    0.869  0.861  0.905
(rows without any history get no score and are left out; counts below. auroc_all: all rows, no history = lowest score)
                    rule split  auroc  auroc_all  scored   of
driver top-3 rate, 365 d train  0.866      0.857    1245 1353
  team top-3 rate, 365 d train  0.869      0.858    1258 1353
last qualifying position train  0.884      0.871    1261 1353
driver top-3 rate, 365 d   val  0.865      0.866     561  588
  team top-3 rate, 365 d   val  0.861      0.861     564  588
last qualifying position   val  0.841      0.841     567  588
driver top-3 rate, 365 d  test  0.906      0.903     700  726
  team top-3 rate, 365 d  test  0.905      0.908     707  726
last qualifying position  test  0.900      0.903     709  726

   per year of the timestamp, AUROC (examples/positives):
   driver top-3 rate, 365 d   val  2005 0.82 (165/37)  2006 0.81 (178/40)  2007 0.96 (201/34)  2008 0.78 (44/8)
   driver top-3 rate, 365 d   test 2010 0.88 (219/38)  2011 0.96 (244/38)  2012 0.87 (241/46)  2013 0.79 (22/6)
   team top-3 rate, 365 d     val  2005 0.75 (165/37)  2006 0.82 (178/40)  2007 0.95 (201/34)  2008 0.87 (44/8)
   team top-3 rate, 365 d     test 2010 0.89 (219/38)  2011 0.97 (244/38)  2012 0.84 (241/46)  2013 0.86 (22/6)
   last qualifying position   val  2005 0.81 (165/37)  2006 0.81 (178/40)  2007 0.93 (201/34)  2008 0.78 (44/8)
   last qualifying position   test 2010 0.92 (219/38)  2011 0.95 (244/38)  2012 0.84 (241/46)  2013 0.84 (22/6)

====================================================================================================
driver-dnf  (target 'did_not_finish', data source {'db': 'cache', 'task': 'local', 'from_cache': True})
====================================================================================================
1. Size of the splits
split  examples  timestamps      first       last  positives  pos_rate  drivers  drivers_with_a_positive  examples_per_driver
train     11411         420 1950-05-20 2004-10-03      10046     0.880      780                      774   14.6
  val       566          26 2005-03-02 2008-03-16        441     0.779       42                       42   13.5
 test       702          29 2010-03-02 2013-03-16        495     0.705       42                       42   16.7

2. Which drivers: overlap between the splits
drivers in val 42, in test 42, in both 21
test examples whose driver is also in val: 60.8%; test positives whose driver is also in val: 53.3%
val positives whose driver is also in test: 54.6%
test drivers never seen in train or val: 21 (39.2% of the test examples)

3. Who the positives are (not finishing)
[val] 441 positives from 42 drivers; top 3 drivers 16%, top 5 26%
   drivers: Takuma Sato 26, Mark Webber 23, Rubens Barrichello 22, Jarno Trulli 22, David Coulthard 22, Ralf Schumacher 22, Christijan Albers 21, Jenson Button 19
   teams:   Williams 47, Toyota 46, Red Bull 45, Super Aguri 36, Toro Rosso 36, Honda 30  (team of the driver's next race)
[test] 495 positives from 42 drivers; top 3 drivers 17%, top 5 25%
   drivers: Timo Glock 28, Heikki Kovalainen 28, Vitaly Petrov 27, Kamui Kobayashi 22, Michael Schumacher 21, Pastor Maldonado 20, Bruno Senna 19, Jarno Trulli 18
   teams:   HRT 60, Williams 51, Sauber 49, Toro Rosso 47, Force India 41, Mercedes 37  (team of the driver's next race)

3b. The 6 drivers with most positives in each split, seen in the other split (examples / positives)
   top of test: Timo Glock 28 in test -> 1/1 in val; Heikki Kovalainen 28 in test -> 10/5 in val; Vitaly Petrov 27 intest -> 0/0 in val; Kamui Kobayashi 22 in test -> 0/0 in val; Michael Schumacher 21 in test -> 16/9 in val; Pastor Maldonado 20 in test -> 0/0 in val
   top of val: Takuma Sato 26 in val -> 0/0 in test; Mark Webber 23 in val -> 29/8 in test; David Coulthard 22 in val-> 0/0 in test; Jarno Trulli 22 in val -> 18/18 in test; Rubens Barrichello 22 in val -> 18/16 in test; Ralf Schumacher 22 in val -> 0/0 in test

4. How predictable each split is with simple rules (AUROC; computed only from data before each timestamp)
   rate, 365 d: share of the driver's (or of his last team's) sessions in the 365 days before the timestamp
   that ended in not finishing; last qualifying position: lower is better
split                         train    val   test
rule                                             
driver no-finish rate, 365 d  0.777  0.789  0.815
team no-finish rate, 365 d    0.786  0.770  0.824
(rows without any history get no score and are left out; counts below. auroc_all: all rows, no history = lowest score)
                        rule split  auroc  auroc_all  scored    of
driver no-finish rate, 365 d train  0.777      0.711   10389 11411
  team no-finish rate, 365 d train  0.786      0.729   10567 11411
driver no-finish rate, 365 d   val  0.789      0.762     539   566
  team no-finish rate, 365 d   val  0.770      0.744     543   566
driver no-finish rate, 365 d  test  0.815      0.780     676   702
  team no-finish rate, 365 d  test  0.824      0.795     683   702

   per year of the timestamp, AUROC (examples/positives):
   driver no-finish rate, 365 d val  2005 0.68 (165/130)  2006 0.84 (178/144)  2007 0.82 (201/148)  2008 0.85 (22/19)
   driver no-finish rate, 365 d test 2010 0.77 (219/158)  2011 0.93 (220/172)  2012 0.77 (241/150)  2013 0.53 (22/15)
   team no-finish rate, 365 d val  2005 0.57 (165/130)  2006 0.85 (178/144)  2007 0.83 (201/148)  2008 0.82 (22/19)
   team no-finish rate, 365 d test 2010 0.79 (219/158)  2011 0.93 (220/172)  2012 0.77 (241/150)  2013 0.55 (22/15)

====================================================================================================
5. How Formula 1 changed per season (from the database)
====================================================================================================
      races_with_qualifying  mean_cars_in_qualifying  teams  drivers  drivers_in_top3  top_team_share_of_top3  top_team  finished_share
year                 
1998                      7                     21.9     11       23                8                    0.57   McLaren            0.25
1999                      3                     21.7     11       24                4                    0.67   McLaren            0.33
2000                      4                     22.0     11       22                5                    0.58   McLaren            0.28
2001                      1                     22.0     11       22                3                    0.67  Williams            0.26
2002                      2                     21.0     11       22                4                    0.67   Ferrari            0.26
2003                     16                     20.0     10       24               11                    0.38   Ferrari            0.33
2004                     18                     20.0     10       25               11                    0.41   Ferrari            0.38
2005                     19                     19.8     10       27               10                    0.35   Renault            0.39
2006                     18                     22.0     12       27               12                    0.37   Ferrari            0.37
2007                     17                     22.0     11       26                5                    0.47   McLaren            0.39
2008                     18                     20.4     11       22                9                    0.43   Ferrari            0.53
2009                     17                     20.0     10       25               14                    0.33  Red Bull            0.63
2010                     19                     24.0     12       27                9                    0.54  Red Bull            0.46
2011                     19                     23.8     12       28                7                    0.54  Red Bull            0.38
2012                     20                     23.8     12       25               11                    0.35   McLaren            0.57
2013                     19                     22.0     11       23               10                    0.46  Red Bull            0.58
2014                     19                     21.3     11       24                7                    0.58  Mercedes            0.49
2015                     19                     19.7     11       22                7                    0.61  Mercedes            0.45
2016                     21                     21.8     11       24                9                    0.60  Mercedes            0.44

splits: train < 2005-01-01 <= val < 2010-01-01 <= test (labels look 30 days ahead of each timestamp)
```
