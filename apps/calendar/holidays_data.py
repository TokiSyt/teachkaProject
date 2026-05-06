"""
Curated holiday data with inline translations.

Data shape:
    DESCRIPTIONS[country][lib_name] = {
        "subject": {"en": ..., "cs": ..., "pt": ...},
        "description": {"en": ..., "cs": ..., "pt": ...},
    }

Lookup at render time via the calendar_tags template filters
(holiday_name / holiday_subject / holiday_description). DB stores English
strings; non-English keys are optional and fall back to "en".

Country code mapping (lib -> our model):
    CZ -> CZ
    PT -> PT
    GB -> EN
"""

NAMES: dict[str, dict[str, str]] = {
    "New Year's Day": {"cs": "Nový rok", "pt": "Ano Novo"},
    "Independent Czech State Restoration Day": {
        "cs": "Den obnovy samostatného českého státu",
        "pt": "Dia da Restauração do Estado Checo Independente",
    },
    "Good Friday": {"cs": "Velký pátek", "pt": "Sexta-feira Santa"},
    "Easter Monday": {"cs": "Velikonoční pondělí", "pt": "Segunda-feira de Páscoa"},
    "Easter Sunday": {"cs": "Velikonoční neděle", "pt": "Domingo de Páscoa"},
    "Labor Day": {"cs": "Svátek práce", "pt": "Dia do Trabalhador"},
    "Victory Day": {"cs": "Den vítězství", "pt": "Dia da Vitória"},
    "Saints Cyril and Methodius Day": {
        "cs": "Den slovanských věrozvěstů Cyrila a Metoděje",
        "pt": "Dia de São Cirilo e Metódio",
    },
    "Jan Hus Day": {"cs": "Den upálení mistra Jana Husa", "pt": "Dia de Jan Hus"},
    "Statehood Day": {"cs": "Den české státnosti", "pt": "Dia da Estatalidade Checa"},
    "Independent Czechoslovak State Day": {
        "cs": "Den vzniku samostatného československého státu",
        "pt": "Dia do Estado Checoslovaco Independente",
    },
    "Struggle for Freedom and Democracy Day and International Students' Day": {
        "cs": "Den boje za svobodu a demokracii a Mezinárodní den studentstva",
        "pt": "Dia da Luta pela Liberdade e Democracia e Dia Internacional do Estudante",
    },
    "Christmas Eve": {"cs": "Štědrý den", "pt": "Véspera de Natal"},
    "Christmas Day": {"cs": "1. svátek vánoční", "pt": "Natal"},
    "Second Day of Christmas": {"cs": "2. svátek vánoční", "pt": "Dia de Santo Estêvão"},
    "Carnival": {"cs": "Karneval", "pt": "Carnaval"},
    "Freedom Day": {"cs": "Den svobody", "pt": "Dia da Liberdade"},
    "Corpus Christi": {"cs": "Svátek Božího Těla", "pt": "Corpo de Deus"},
    "Day of Portugal, Camões, and the Portuguese Communities": {
        "cs": "Den Portugalska",
        "pt": "Dia de Portugal, de Camões e das Comunidades Portuguesas",
    },
    "Assumption Day": {"cs": "Nanebevzetí Panny Marie", "pt": "Assunção de Nossa Senhora"},
    "Republic Day": {"cs": "Den republiky", "pt": "Implantação da República"},
    "All Saints' Day": {"cs": "Svátek Všech svatých", "pt": "Dia de Todos os Santos"},
    "Restoration of Independence Day": {
        "cs": "Den obnovení nezávislosti",
        "pt": "Restauração da Independência",
    },
    "Immaculate Conception": {"cs": "Neposkvrněné početí Panny Marie", "pt": "Imaculada Conceição"},
    "May Day": {"cs": "Prvomájový svátek", "pt": "Feriado de Maio"},
    "Spring Bank Holiday": {"cs": "Jarní svátek", "pt": "Feriado da Primavera"},
    "Late Summer Bank Holiday": {"cs": "Letní svátek", "pt": "Feriado de Verão"},
    "Boxing Day": {"cs": "Druhý svátek vánoční", "pt": "Dia das Caixas"},
    "Boxing Day (observed)": {
        "cs": "Druhý svátek vánoční (přesun)",
        "pt": "Dia das Caixas (observado)",
    },
    "Valentine's Day": {"cs": "Valentýn", "pt": "Dia dos Namorados"},
    "International Women's Day": {"cs": "Mezinárodní den žen", "pt": "Dia Internacional da Mulher"},
    "Earth Day": {"cs": "Den Země", "pt": "Dia da Terra"},
    "International Workers' Day": {
        "cs": "Mezinárodní svátek práce",
        "pt": "Dia Internacional dos Trabalhadores",
    },
    "World Environment Day": {
        "cs": "Světový den životního prostředí",
        "pt": "Dia Mundial do Ambiente",
    },
    "International Day of Peace": {
        "cs": "Mezinárodní den míru",
        "pt": "Dia Internacional da Paz",
    },
    "World Teachers' Day": {"cs": "Mezinárodní den učitelů", "pt": "Dia Mundial do Professor"},
    "Human Rights Day": {"cs": "Den lidských práv", "pt": "Dia dos Direitos Humanos"},
}


DESCRIPTIONS: dict[str, dict[str, dict[str, dict[str, str]]]] = {
    "CZ": {
        "New Year's Day": {
            "subject": {"en": "New Year's Day", "cs": "Nový rok", "pt": "Ano Novo"},
            "description": {
                "en": "Marks the start of the new calendar year.",
                "cs": "Označuje začátek nového kalendářního roku.",
                "pt": "Marca o início do novo ano civil.",
            },
        },
        "Independent Czech State Restoration Day": {
            "subject": {
                "en": "Restoration Day of the Independent Czech State",
                "cs": "Den obnovy samostatného českého státu",
                "pt": "Dia da Restauração do Estado Checo Independente",
            },
            "description": {
                "en": (
                    "Commemorates the restoration of the independent Czech state on "
                    "1 January 1993, the day the Czech Republic and Slovakia peacefully "
                    "separated."
                ),
                "cs": (
                    "Připomíná obnovu samostatného českého státu 1. ledna 1993, den, "
                    "kdy se Česká republika a Slovensko pokojně rozdělily."
                ),
                "pt": (
                    "Comemora a restauração do Estado checo independente a 1 de janeiro "
                    "de 1993, dia em que a República Checa e a Eslováquia se separaram "
                    "pacificamente."
                ),
            },
        },
        "Good Friday": {
            "subject": {"en": "Good Friday", "cs": "Velký pátek", "pt": "Sexta-feira Santa"},
            "description": {
                "en": (
                    "Christian holy day commemorating the crucifixion of Jesus Christ. "
                    "Re-introduced as a public holiday in the Czech Republic in 2016."
                ),
                "cs": (
                    "Křesťanský svátek připomínající ukřižování Ježíše Krista. "
                    "V České republice znovu zaveden jako státní svátek v roce 2016."
                ),
                "pt": (
                    "Dia santo cristão que comemora a crucificação de Jesus Cristo. "
                    "Reintroduzido como feriado nacional na República Checa em 2016."
                ),
            },
        },
        "Easter Monday": {
            "subject": {
                "en": "Easter Monday",
                "cs": "Velikonoční pondělí",
                "pt": "Segunda-feira de Páscoa",
            },
            "description": {
                "en": (
                    "Traditional Czech Easter celebration. Boys go from house to house "
                    "with decorated willow whips (pomlázka) symbolically whipping girls "
                    "for health and youth, receiving painted eggs in return."
                ),
                "cs": (
                    "Tradiční české velikonoční oslavy. Chlapci chodí dům od domu "
                    "s pomlázkou ze zdobených vrbových proutků a symbolicky šlehají "
                    "dívky pro zdraví a mládí, na oplátku dostávají malovaná vajíčka."
                ),
                "pt": (
                    "Celebração tradicional da Páscoa checa. Os rapazes vão de casa em "
                    "casa com chicotes de salgueiro decorados (pomlázka), batendo "
                    "simbolicamente nas raparigas para lhes dar saúde e juventude, "
                    "recebendo em troca ovos pintados."
                ),
            },
        },
        "Labor Day": {
            "subject": {"en": "Labour Day", "cs": "Svátek práce", "pt": "Dia do Trabalhador"},
            "description": {
                "en": (
                    "International Workers' Day, celebrating workers' rights and the "
                    "labour movement. In Czech tradition also a day for couples to kiss "
                    "under a blooming cherry tree."
                ),
                "cs": (
                    "Mezinárodní svátek práce, oslava práv pracujících a dělnického "
                    "hnutí. V české tradici také den, kdy se páry líbají pod rozkvetlou "
                    "třešní."
                ),
                "pt": (
                    "Dia Internacional dos Trabalhadores, celebra os direitos dos "
                    "trabalhadores e o movimento operário. Na tradição checa também o "
                    "dia em que os casais se beijam sob uma cerejeira em flor."
                ),
            },
        },
        "Victory Day": {
            "subject": {
                "en": "Liberation Day / Victory in Europe Day",
                "cs": "Den vítězství",
                "pt": "Dia da Vitória na Europa",
            },
            "description": {
                "en": (
                    "Commemorates the end of World War II in Europe on 8 May 1945 and "
                    "the liberation of Czechoslovakia from Nazi occupation."
                ),
                "cs": (
                    "Připomíná konec druhé světové války v Evropě 8. května 1945 "
                    "a osvobození Československa od nacistické okupace."
                ),
                "pt": (
                    "Comemora o fim da Segunda Guerra Mundial na Europa a 8 de maio de "
                    "1945 e a libertação da Checoslováquia da ocupação nazi."
                ),
            },
        },
        "Saints Cyril and Methodius Day": {
            "subject": {
                "en": "Saints Cyril and Methodius Day",
                "cs": "Den slovanských věrozvěstů Cyrila a Metoděje",
                "pt": "Dia de São Cirilo e Metódio",
            },
            "description": {
                "en": (
                    "Honours the Byzantine missionaries who brought Christianity and "
                    "the Glagolitic alphabet to the Slavs in 863, founding Slavic "
                    "literary tradition."
                ),
                "cs": (
                    "Uctívá byzantské misionáře, kteří v roce 863 přinesli Slovanům "
                    "křesťanství a hlaholici a založili slovanskou literární tradici."
                ),
                "pt": (
                    "Honra os missionários bizantinos que em 863 trouxeram o "
                    "cristianismo e o alfabeto glagolítico aos eslavos, fundando a "
                    "tradição literária eslava."
                ),
            },
        },
        "Jan Hus Day": {
            "subject": {
                "en": "Jan Hus Day",
                "cs": "Den upálení mistra Jana Husa",
                "pt": "Dia de Jan Hus",
            },
            "description": {
                "en": (
                    "Anniversary of the burning at the stake of Jan Hus in 1415, the "
                    "Czech religious reformer whose teachings preceded the Protestant "
                    "Reformation by a century."
                ),
                "cs": (
                    "Výročí upálení Jana Husa v roce 1415, českého náboženského "
                    "reformátora, jehož učení o století předcházelo protestantskou "
                    "reformaci."
                ),
                "pt": (
                    "Aniversário da morte na fogueira de Jan Hus em 1415, reformador "
                    "religioso checo cujos ensinamentos precederam em um século a "
                    "Reforma Protestante."
                ),
            },
        },
        "Statehood Day": {
            "subject": {
                "en": "Czech Statehood Day (Saint Wenceslas Day)",
                "cs": "Den české státnosti (svatého Václava)",
                "pt": "Dia da Estatalidade Checa (São Venceslau)",
            },
            "description": {
                "en": (
                    "Honours Saint Wenceslas, patron saint of the Czech lands and "
                    "symbol of Czech statehood, killed by his brother Boleslav in 935."
                ),
                "cs": (
                    "Uctívá svatého Václava, patrona českých zemí a symbol české "
                    "státnosti, zavražděného svým bratrem Boleslavem v roce 935."
                ),
                "pt": (
                    "Honra São Venceslau, padroeiro das terras checas e símbolo da "
                    "soberania checa, morto pelo seu irmão Boleslau em 935."
                ),
            },
        },
        "Independent Czechoslovak State Day": {
            "subject": {
                "en": "Independent Czechoslovak State Day",
                "cs": "Den vzniku samostatného československého státu",
                "pt": "Dia do Estado Checoslovaco Independente",
            },
            "description": {
                "en": (
                    "Marks the founding of independent Czechoslovakia on 28 October "
                    "1918 after the collapse of the Austro-Hungarian Empire at the end "
                    "of WWI."
                ),
                "cs": (
                    "Připomíná založení samostatného Československa 28. října 1918 "
                    "po rozpadu Rakouska-Uherska na konci první světové války."
                ),
                "pt": (
                    "Marca a fundação da Checoslováquia independente a 28 de outubro "
                    "de 1918, após o colapso do Império Austro-Húngaro no final da "
                    "Primeira Guerra Mundial."
                ),
            },
        },
        "Struggle for Freedom and Democracy Day and International Students' Day": {
            "subject": {
                "en": "Struggle for Freedom and Democracy Day / International Students' Day",
                "cs": "Den boje za svobodu a demokracii a Mezinárodní den studentstva",
                "pt": "Dia da Luta pela Liberdade e Democracia / Dia Internacional do Estudante",
            },
            "description": {
                "en": (
                    "Commemorates two student demonstrations: the 1939 protest against "
                    "Nazi occupation and the 1989 march that triggered the Velvet "
                    "Revolution and ended communist rule in Czechoslovakia."
                ),
                "cs": (
                    "Připomíná dvě studentské demonstrace: protest z roku 1939 proti "
                    "nacistické okupaci a pochod z roku 1989, který odstartoval "
                    "sametovou revoluci a ukončil komunistickou vládu v Československu."
                ),
                "pt": (
                    "Comemora duas manifestações estudantis: o protesto de 1939 contra "
                    "a ocupação nazi e a marcha de 1989 que desencadeou a Revolução de "
                    "Veludo e pôs fim ao regime comunista na Checoslováquia."
                ),
            },
        },
        "Christmas Eve": {
            "subject": {
                "en": "Christmas Eve",
                "cs": "Štědrý den",
                "pt": "Véspera de Natal",
            },
            "description": {
                "en": (
                    "The main day of Czech Christmas, when families share a traditional "
                    "dinner of carp and potato salad, and presents are brought by "
                    "Ježíšek (Baby Jesus) rather than Santa Claus."
                ),
                "cs": (
                    "Hlavní den českých Vánoc, kdy rodiny společně večeří tradičního "
                    "kapra s bramborovým salátem a dárky nosí Ježíšek, nikoli Santa "
                    "Claus."
                ),
                "pt": (
                    "Dia principal do Natal checo, em que as famílias partilham um "
                    "jantar tradicional de carpa e salada de batata; os presentes são "
                    "trazidos por Ježíšek (Menino Jesus) em vez do Pai Natal."
                ),
            },
        },
        "Christmas Day": {
            "subject": {"en": "Christmas Day", "cs": "1. svátek vánoční", "pt": "Natal"},
            "description": {
                "en": "Christian feast celebrating the birth of Jesus Christ.",
                "cs": "Křesťanský svátek oslavující narození Ježíše Krista.",
                "pt": "Festa cristã que celebra o nascimento de Jesus Cristo.",
            },
        },
        "Second Day of Christmas": {
            "subject": {
                "en": "Saint Stephen's Day / Second Day of Christmas",
                "cs": "2. svátek vánoční (svatého Štěpána)",
                "pt": "Dia de Santo Estêvão",
            },
            "description": {
                "en": (
                    "Commemorates Saint Stephen, the first Christian martyr, and "
                    "traditionally a day of carolling and visiting family in the Czech "
                    "Republic."
                ),
                "cs": (
                    "Připomíná svatého Štěpána, prvního křesťanského mučedníka, "
                    "a v České republice tradiční den koled a návštěv rodiny."
                ),
                "pt": (
                    "Comemora Santo Estêvão, o primeiro mártir cristão; "
                    "tradicionalmente um dia de cantares de Natal e visitas à família "
                    "na República Checa."
                ),
            },
        },
    },
    "PT": {
        "New Year's Day": {
            "subject": {"en": "New Year's Day", "cs": "Nový rok", "pt": "Ano Novo"},
            "description": {
                "en": "Celebration of the start of the new calendar year.",
                "cs": "Oslava začátku nového kalendářního roku.",
                "pt": "Celebração do início do novo ano civil.",
            },
        },
        "Carnival": {
            "subject": {"en": "Carnival", "cs": "Karneval", "pt": "Carnaval (Entrudo)"},
            "description": {
                "en": (
                    "Festive season before Lent featuring parades, costumes and street "
                    "parties. Optional municipal holiday in Portugal, widely observed."
                ),
                "cs": (
                    "Slavnostní období před postem s průvody, kostýmy a pouličními "
                    "zábavami. V Portugalsku nepovinný městský svátek, široce slavený."
                ),
                "pt": (
                    "Época festiva antes da Quaresma, com desfiles, fantasias e festas "
                    "de rua. Feriado municipal facultativo em Portugal, amplamente "
                    "observado."
                ),
            },
        },
        "Good Friday": {
            "subject": {"en": "Good Friday", "cs": "Velký pátek", "pt": "Sexta-feira Santa"},
            "description": {
                "en": (
                    "Christian holy day commemorating the crucifixion of Jesus Christ, "
                    "marked by solemn processions across Portugal."
                ),
                "cs": (
                    "Křesťanský svátek připomínající ukřižování Ježíše Krista, "
                    "v Portugalsku doprovázený slavnostními procesími."
                ),
                "pt": (
                    "Dia santo cristão que comemora a crucificação de Jesus Cristo, "
                    "assinalado por solenes procissões por todo o país."
                ),
            },
        },
        "Easter Sunday": {
            "subject": {
                "en": "Easter Sunday",
                "cs": "Velikonoční neděle",
                "pt": "Domingo de Páscoa",
            },
            "description": {
                "en": (
                    "Christian celebration of the resurrection of Jesus Christ. "
                    "Families gather for a traditional lunch featuring folar, a sweet "
                    "bread with eggs."
                ),
                "cs": (
                    "Křesťanská oslava zmrtvýchvstání Ježíše Krista. Rodiny se "
                    "scházejí k tradičnímu obědu s folarem, sladkým chlebem s vejci."
                ),
                "pt": (
                    "Celebração cristã da ressurreição de Jesus Cristo. As famílias "
                    "reúnem-se para um almoço tradicional com folar, um pão doce com "
                    "ovos."
                ),
            },
        },
        "Freedom Day": {
            "subject": {
                "en": "Freedom Day",
                "cs": "Den svobody",
                "pt": "Dia da Liberdade",
            },
            "description": {
                "en": (
                    "Commemorates the Carnation Revolution of 25 April 1974, a "
                    "peaceful military coup that ended the Estado Novo dictatorship "
                    "and led to democracy in Portugal."
                ),
                "cs": (
                    "Připomíná Karafiátovou revoluci z 25. dubna 1974, pokojný "
                    "vojenský převrat, který ukončil diktaturu Estado Novo a přinesl "
                    "Portugalsku demokracii."
                ),
                "pt": (
                    "Comemora a Revolução dos Cravos de 25 de Abril de 1974, um "
                    "golpe militar pacífico que pôs fim à ditadura do Estado Novo e "
                    "trouxe a democracia a Portugal."
                ),
            },
        },
        "Labor Day": {
            "subject": {"en": "Labour Day", "cs": "Svátek práce", "pt": "Dia do Trabalhador"},
            "description": {
                "en": "International Workers' Day, celebrating workers' rights.",
                "cs": "Mezinárodní svátek práce, oslava práv pracujících.",
                "pt": "Dia Internacional dos Trabalhadores, celebra os direitos dos trabalhadores.",
            },
        },
        "Corpus Christi": {
            "subject": {
                "en": "Corpus Christi",
                "cs": "Svátek Božího Těla",
                "pt": "Corpo de Deus",
            },
            "description": {
                "en": (
                    "Catholic feast honouring the Eucharist. Marked by religious "
                    "processions through Portuguese towns and cities."
                ),
                "cs": (
                    "Katolický svátek na počest eucharistie. Doprovázen náboženskými procesími v portugalských městech."
                ),
                "pt": (
                    "Festa católica em honra da Eucaristia. Assinalada com procissões "
                    "religiosas pelas vilas e cidades portuguesas."
                ),
            },
        },
        "Day of Portugal, Camões, and the Portuguese Communities": {
            "subject": {
                "en": "Portugal Day",
                "cs": "Den Portugalska",
                "pt": "Dia de Portugal, de Camões e das Comunidades",
            },
            "description": {
                "en": (
                    "National day commemorating the death of poet Luís de Camões in "
                    "1580, author of Os Lusíadas. Honours Portugal, its culture and "
                    "the global Portuguese diaspora."
                ),
                "cs": (
                    "Národní den připomínající smrt básníka Luíse de Camõese v roce "
                    "1580, autora Lusovců. Uctívá Portugalsko, jeho kulturu "
                    "a celosvětovou portugalskou diasporu."
                ),
                "pt": (
                    "Dia nacional que comemora a morte do poeta Luís de Camões em "
                    "1580, autor d'Os Lusíadas. Homenageia Portugal, a sua cultura "
                    "e a diáspora portuguesa pelo mundo."
                ),
            },
        },
        "Assumption Day": {
            "subject": {
                "en": "Assumption of Mary",
                "cs": "Nanebevzetí Panny Marie",
                "pt": "Assunção de Nossa Senhora",
            },
            "description": {
                "en": "Catholic feast celebrating the bodily assumption of the Virgin Mary into heaven.",
                "cs": "Katolický svátek oslavující tělesné nanebevzetí Panny Marie.",
                "pt": "Festa católica que celebra a assunção corporal da Virgem Maria ao céu.",
            },
        },
        "Republic Day": {
            "subject": {
                "en": "Republic Day",
                "cs": "Den republiky",
                "pt": "Implantação da República",
            },
            "description": {
                "en": (
                    "Commemorates the 5 October 1910 revolution that overthrew the "
                    "Portuguese monarchy and established the First Portuguese Republic."
                ),
                "cs": (
                    "Připomíná revoluci z 5. října 1910, která svrhla portugalskou "
                    "monarchii a založila První portugalskou republiku."
                ),
                "pt": (
                    "Comemora a revolução de 5 de outubro de 1910 que derrubou a "
                    "monarquia portuguesa e estabeleceu a Primeira República Portuguesa."
                ),
            },
        },
        "All Saints' Day": {
            "subject": {
                "en": "All Saints' Day",
                "cs": "Svátek Všech svatých",
                "pt": "Dia de Todos os Santos",
            },
            "description": {
                "en": (
                    "Catholic feast honouring all saints. Families traditionally visit "
                    "cemeteries to remember deceased relatives."
                ),
                "cs": (
                    "Katolický svátek všech svatých. Rodiny tradičně navštěvují "
                    "hřbitovy a vzpomínají na zesnulé příbuzné."
                ),
                "pt": (
                    "Festa católica em honra de todos os santos. As famílias visitam "
                    "tradicionalmente os cemitérios para recordar os familiares "
                    "falecidos."
                ),
            },
        },
        "Restoration of Independence Day": {
            "subject": {
                "en": "Restoration of Independence Day",
                "cs": "Den obnovení nezávislosti",
                "pt": "Restauração da Independência",
            },
            "description": {
                "en": (
                    "Marks the 1 December 1640 uprising that ended sixty years of "
                    "Iberian Union with Spain and restored Portuguese independence "
                    "under the House of Braganza."
                ),
                "cs": (
                    "Připomíná povstání 1. prosince 1640, které ukončilo šedesát let "
                    "Iberské unie se Španělskem a obnovilo portugalskou nezávislost "
                    "pod dynastií Braganza."
                ),
                "pt": (
                    "Marca o levantamento de 1 de dezembro de 1640, que pôs fim a "
                    "sessenta anos de União Ibérica com Espanha e restaurou a "
                    "independência de Portugal sob a Casa de Bragança."
                ),
            },
        },
        "Immaculate Conception": {
            "subject": {
                "en": "Immaculate Conception",
                "cs": "Neposkvrněné početí Panny Marie",
                "pt": "Imaculada Conceição",
            },
            "description": {
                "en": (
                    "Catholic feast celebrating the conception of the Virgin Mary "
                    "free of original sin. Our Lady of the Immaculate Conception is "
                    "the patron saint of Portugal."
                ),
                "cs": (
                    "Katolický svátek oslavující početí Panny Marie bez prvotního "
                    "hříchu. Panna Maria Neposkvrněného Početí je patronka Portugalska."
                ),
                "pt": (
                    "Festa católica que celebra a conceição da Virgem Maria livre do "
                    "pecado original. Nossa Senhora da Imaculada Conceição é a "
                    "padroeira de Portugal."
                ),
            },
        },
        "Christmas Day": {
            "subject": {"en": "Christmas Day", "cs": "Vánoce", "pt": "Natal"},
            "description": {
                "en": (
                    "Christian feast celebrating the birth of Jesus Christ. "
                    "Portuguese families traditionally gather for a Christmas Eve "
                    "supper of bacalhau (salt cod) and exchange gifts at midnight."
                ),
                "cs": (
                    "Křesťanský svátek oslavující narození Ježíše Krista. "
                    "Portugalské rodiny tradičně večeří o Štědrém večeru bacalhau "
                    "(sušená treska) a o půlnoci si vyměňují dárky."
                ),
                "pt": (
                    "Festa cristã que celebra o nascimento de Jesus Cristo. As "
                    "famílias portuguesas reúnem-se tradicionalmente na consoada "
                    "para uma ceia de bacalhau e trocam presentes à meia-noite."
                ),
            },
        },
    },
    "EN": {
        "New Year's Day": {
            "subject": {"en": "New Year's Day", "cs": "Nový rok", "pt": "Ano Novo"},
            "description": {
                "en": "Celebration of the start of the new calendar year.",
                "cs": "Oslava začátku nového kalendářního roku.",
                "pt": "Celebração do início do novo ano civil.",
            },
        },
        "Good Friday": {
            "subject": {"en": "Good Friday", "cs": "Velký pátek", "pt": "Sexta-feira Santa"},
            "description": {
                "en": "Christian holy day commemorating the crucifixion of Jesus Christ.",
                "cs": "Křesťanský svátek připomínající ukřižování Ježíše Krista.",
                "pt": "Dia santo cristão que comemora a crucificação de Jesus Cristo.",
            },
        },
        "Easter Monday": {
            "subject": {
                "en": "Easter Monday",
                "cs": "Velikonoční pondělí",
                "pt": "Segunda-feira de Páscoa",
            },
            "description": {
                "en": "The day after Easter Sunday, traditionally a day of rest following Easter celebrations.",
                "cs": "Den po velikonoční neděli, tradičně den odpočinku po velikonočních oslavách.",
                "pt": (
                    "O dia a seguir ao Domingo de Páscoa, tradicionalmente um dia "
                    "de descanso após as celebrações pascais."
                ),
            },
        },
        "May Day": {
            "subject": {
                "en": "Early May Bank Holiday",
                "cs": "Prvomájový svátek",
                "pt": "Feriado de Maio",
            },
            "description": {
                "en": (
                    "Bank holiday on the first Monday of May, with roots in ancient "
                    "spring festivals and the modern labour movement."
                ),
                "cs": (
                    "Státní svátek prvního pondělí v květnu, s kořeny ve starých "
                    "jarních oslavách a v moderním dělnickém hnutí."
                ),
                "pt": (
                    "Feriado bancário na primeira segunda-feira de maio, com raízes "
                    "em antigas festas de primavera e no movimento operário moderno."
                ),
            },
        },
        "Spring Bank Holiday": {
            "subject": {
                "en": "Spring Bank Holiday",
                "cs": "Jarní svátek",
                "pt": "Feriado da Primavera",
            },
            "description": {
                "en": "Bank holiday on the last Monday of May. Replaced the moveable Whit Monday in 1971.",
                "cs": "Státní svátek posledního pondělí v květnu. V roce 1971 nahradil pohyblivé pondělí svatodušní.",
                "pt": "Feriado bancário na última segunda-feira de maio. Substituiu o Pentecostes móvel em 1971.",
            },
        },
        "Late Summer Bank Holiday": {
            "subject": {
                "en": "Summer Bank Holiday",
                "cs": "Letní svátek",
                "pt": "Feriado de Verão",
            },
            "description": {
                "en": "Bank holiday on the last Monday of August, marking the unofficial end of summer in England.",
                "cs": "Státní svátek posledního pondělí v srpnu, neoficiální konec léta v Anglii.",
                "pt": "Feriado bancário na última segunda-feira de agosto, marcando o fim oficioso do verão em Inglaterra.",
            },
        },
        "Christmas Day": {
            "subject": {"en": "Christmas Day", "cs": "Vánoce", "pt": "Natal"},
            "description": {
                "en": "Christian feast celebrating the birth of Jesus Christ.",
                "cs": "Křesťanský svátek oslavující narození Ježíše Krista.",
                "pt": "Festa cristã que celebra o nascimento de Jesus Cristo.",
            },
        },
        "Boxing Day": {
            "subject": {"en": "Boxing Day", "cs": "Druhý svátek vánoční", "pt": "Dia das Caixas"},
            "description": {
                "en": (
                    "Day after Christmas, originally when servants and tradespeople "
                    "received gift boxes from employers and customers."
                ),
                "cs": (
                    "Den po Vánocích, původně den, kdy služebnictvo a řemeslníci "
                    "dostávali dárkové krabice od zaměstnavatelů a zákazníků."
                ),
                "pt": (
                    "Dia a seguir ao Natal, originalmente quando os criados e "
                    "trabalhadores recebiam caixas de presentes de patrões e clientes."
                ),
            },
        },
        "Boxing Day (observed)": {
            "subject": {
                "en": "Boxing Day (observed)",
                "cs": "Druhý svátek vánoční (přesun)",
                "pt": "Dia das Caixas (observado)",
            },
            "description": {
                "en": "Bank holiday substituted for Boxing Day when it falls on a weekend.",
                "cs": "Náhradní státní svátek za Druhý svátek vánoční, když připadne na víkend.",
                "pt": "Feriado bancário substituto do Dia das Caixas quando este cai ao fim de semana.",
            },
        },
    },
}


# International holidays. Fixed-date global observances used everywhere.
# Format: (month, day, name, subject_dict, description_dict)
INTERNATIONAL_HOLIDAYS: list[tuple[int, int, str, dict[str, str], dict[str, str]]] = [
    (
        1,
        1,
        "New Year's Day",
        {"en": "New Year's Day", "cs": "Nový rok", "pt": "Ano Novo"},
        {
            "en": "Global celebration marking the first day of the Gregorian calendar year.",
            "cs": "Celosvětová oslava prvního dne gregoriánského kalendářního roku.",
            "pt": "Celebração global que marca o primeiro dia do ano do calendário gregoriano.",
        },
    ),
    (
        2,
        14,
        "Valentine's Day",
        {"en": "Saint Valentine's Day", "cs": "Svatý Valentýn", "pt": "Dia de São Valentim"},
        {
            "en": "Day celebrating romantic love, named after the Christian martyr Saint Valentine.",
            "cs": "Den oslavující romantickou lásku, pojmenovaný po křesťanském mučedníkovi svatém Valentýnovi.",
            "pt": "Dia que celebra o amor romântico, com o nome do mártir cristão São Valentim.",
        },
    ),
    (
        3,
        8,
        "International Women's Day",
        {
            "en": "International Women's Day",
            "cs": "Mezinárodní den žen",
            "pt": "Dia Internacional da Mulher",
        },
        {
            "en": (
                "United Nations day celebrating women's rights, achievements and the "
                "ongoing fight for gender equality. Originated in the early 20th "
                "century labour movement."
            ),
            "cs": (
                "Den OSN oslavující práva žen, jejich úspěchy a pokračující boj "
                "za rovnost pohlaví. Vznikl v dělnickém hnutí počátku 20. století."
            ),
            "pt": (
                "Dia das Nações Unidas que celebra os direitos das mulheres, as suas "
                "conquistas e a luta contínua pela igualdade de género. Teve origem "
                "no movimento operário do início do século XX."
            ),
        },
    ),
    (
        4,
        22,
        "Earth Day",
        {"en": "Earth Day", "cs": "Den Země", "pt": "Dia da Terra"},
        {
            "en": "Annual event demonstrating support for environmental protection, first held on 22 April 1970.",
            "cs": "Každoroční událost na podporu ochrany životního prostředí, poprvé pořádaná 22. dubna 1970.",
            "pt": "Evento anual de apoio à proteção ambiental, realizado pela primeira vez a 22 de abril de 1970.",
        },
    ),
    (
        5,
        1,
        "International Workers' Day",
        {
            "en": "International Workers' Day / Labour Day",
            "cs": "Mezinárodní svátek práce",
            "pt": "Dia Internacional dos Trabalhadores",
        },
        {
            "en": "Worldwide celebration of the labour movement, commemorating the 1886 Haymarket affair in Chicago.",
            "cs": "Celosvětová oslava dělnického hnutí, připomínající Haymarketskou aféru z roku 1886 v Chicagu.",
            "pt": "Celebração mundial do movimento operário, em memória do Caso Haymarket de 1886 em Chicago.",
        },
    ),
    (
        6,
        5,
        "World Environment Day",
        {
            "en": "World Environment Day",
            "cs": "Světový den životního prostředí",
            "pt": "Dia Mundial do Ambiente",
        },
        {
            "en": "United Nations day for encouraging awareness and action to protect the environment.",
            "cs": "Den OSN podporující povědomí a opatření k ochraně životního prostředí.",
            "pt": "Dia das Nações Unidas para promover a consciencialização e a ação na proteção do ambiente.",
        },
    ),
    (
        9,
        21,
        "International Day of Peace",
        {
            "en": "International Day of Peace",
            "cs": "Mezinárodní den míru",
            "pt": "Dia Internacional da Paz",
        },
        {
            "en": (
                "United Nations day devoted to strengthening the ideals of peace, "
                "observed by a global ceasefire and non-violence."
            ),
            "cs": ("Den OSN věnovaný posílení ideálů míru, slavený celosvětovým příměřím a nenásilím."),
            "pt": (
                "Dia das Nações Unidas dedicado ao reforço dos ideais de paz, "
                "assinalado por um cessar-fogo global e pela não-violência."
            ),
        },
    ),
    (
        10,
        5,
        "World Teachers' Day",
        {
            "en": "World Teachers' Day",
            "cs": "Mezinárodní den učitelů",
            "pt": "Dia Mundial do Professor",
        },
        {
            "en": "UNESCO day celebrating the role of teachers in providing quality education.",
            "cs": "Den UNESCO oslavující roli učitelů při poskytování kvalitního vzdělání.",
            "pt": "Dia da UNESCO que celebra o papel dos professores na garantia de uma educação de qualidade.",
        },
    ),
    (
        12,
        10,
        "Human Rights Day",
        {"en": "Human Rights Day", "cs": "Den lidských práv", "pt": "Dia dos Direitos Humanos"},
        {
            "en": "Marks the adoption of the Universal Declaration of Human Rights by the UN General Assembly in 1948.",
            "cs": "Připomíná přijetí Všeobecné deklarace lidských práv Valným shromážděním OSN v roce 1948.",
            "pt": "Marca a adoção da Declaração Universal dos Direitos Humanos pela Assembleia Geral da ONU em 1948.",
        },
    ),
    (
        12,
        25,
        "Christmas Day",
        {"en": "Christmas Day", "cs": "Vánoce", "pt": "Natal"},
        {
            "en": "Christian feast celebrating the birth of Jesus Christ, observed as a public holiday in much of the world.",
            "cs": "Křesťanský svátek oslavující narození Ježíše Krista, slavený jako státní svátek ve velké části světa.",
            "pt": "Festa cristã que celebra o nascimento de Jesus Cristo, feriado nacional em grande parte do mundo.",
        },
    ),
]
