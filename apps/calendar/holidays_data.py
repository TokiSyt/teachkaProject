"""
Curated descriptions for holidays and the international holiday list.

Descriptions keyed by the English name returned by the `holidays` library
(`holidays.country_holidays(code, language='en')`). If a holiday name from the
library is missing here, the sync command falls back to an empty description.

Country code mapping (lib -> our model):
    CZ -> CZ
    PT -> PT
    GB -> EN
"""

DESCRIPTIONS: dict[str, dict[str, dict[str, str]]] = {
    "CZ": {
        "New Year's Day": {
            "subject": "New Year's Day / Restoration Day of the Independent Czech State",
            "description": (
                "Marks the start of the new calendar year and, since 2000, also commemorates "
                "the restoration of the independent Czech state on 1 January 1993, the day the "
                "Czech Republic and Slovakia peacefully separated."
            ),
        },
        "Good Friday": {
            "subject": "Good Friday",
            "description": (
                "Christian holy day commemorating the crucifixion of Jesus Christ. "
                "Re-introduced as a public holiday in the Czech Republic in 2016."
            ),
        },
        "Easter Monday": {
            "subject": "Easter Monday",
            "description": (
                "Traditional Czech Easter celebration. Boys go from house to house with "
                "decorated willow whips (pomlázka) symbolically whipping girls for health "
                "and youth, receiving painted eggs in return."
            ),
        },
        "Labor Day": {
            "subject": "Labour Day",
            "description": (
                "International Workers' Day, celebrating workers' rights and the labour "
                "movement. In Czech tradition also a day for couples to kiss under a "
                "blooming cherry tree."
            ),
        },
        "Victory Day": {
            "subject": "Liberation Day / Victory in Europe Day",
            "description": (
                "Commemorates the end of World War II in Europe on 8 May 1945 and the "
                "liberation of Czechoslovakia from Nazi occupation."
            ),
        },
        "Saints Cyril and Methodius Day": {
            "subject": "Saints Cyril and Methodius Day",
            "description": (
                "Honours the Byzantine missionaries who brought Christianity and the "
                "Glagolitic alphabet to the Slavs in 863, founding Slavic literary "
                "tradition."
            ),
        },
        "Jan Hus Day": {
            "subject": "Jan Hus Day",
            "description": (
                "Anniversary of the burning at the stake of Jan Hus in 1415, the Czech "
                "religious reformer whose teachings preceded the Protestant Reformation "
                "by a century."
            ),
        },
        "Statehood Day": {
            "subject": "Czech Statehood Day (Saint Wenceslas Day)",
            "description": (
                "Honours Saint Wenceslas, patron saint of the Czech lands and symbol of "
                "Czech statehood, killed by his brother Boleslav in 935."
            ),
        },
        "Independent Czechoslovak State Day": {
            "subject": "Independent Czechoslovak State Day",
            "description": (
                "Marks the founding of independent Czechoslovakia on 28 October 1918 "
                "after the collapse of the Austro-Hungarian Empire at the end of WWI."
            ),
        },
        "Struggle for Freedom and Democracy Day": {
            "subject": "Struggle for Freedom and Democracy Day",
            "description": (
                "Commemorates two student demonstrations: the 1939 protest against Nazi "
                "occupation and the 1989 march that triggered the Velvet Revolution and "
                "ended communist rule in Czechoslovakia."
            ),
        },
        "Christmas Eve": {
            "subject": "Christmas Eve (Štědrý den)",
            "description": (
                "The main day of Czech Christmas, when families share a traditional dinner "
                "of carp and potato salad, and presents are brought by Ježíšek (Baby Jesus) "
                "rather than Santa Claus."
            ),
        },
        "Christmas Day": {
            "subject": "Christmas Day",
            "description": "Christian feast celebrating the birth of Jesus Christ.",
        },
        "Second Day of Christmas": {
            "subject": "Saint Stephen's Day / Second Day of Christmas",
            "description": (
                "Commemorates Saint Stephen, the first Christian martyr, and traditionally "
                "a day of carolling and visiting family in the Czech Republic."
            ),
        },
    },
    "PT": {
        "New Year's Day": {
            "subject": "New Year's Day (Ano Novo)",
            "description": "Celebration of the start of the new calendar year.",
        },
        "Carnival": {
            "subject": "Carnival (Entrudo)",
            "description": (
                "Festive season before Lent featuring parades, costumes and street parties. "
                "Optional municipal holiday in Portugal, widely observed."
            ),
        },
        "Good Friday": {
            "subject": "Good Friday (Sexta-feira Santa)",
            "description": (
                "Christian holy day commemorating the crucifixion of Jesus Christ, "
                "marked by solemn processions across Portugal."
            ),
        },
        "Easter Sunday": {
            "subject": "Easter Sunday (Páscoa)",
            "description": (
                "Christian celebration of the resurrection of Jesus Christ. Families "
                "gather for a traditional lunch featuring folar, a sweet bread with eggs."
            ),
        },
        "Freedom Day": {
            "subject": "Freedom Day (Dia da Liberdade)",
            "description": (
                "Commemorates the Carnation Revolution of 25 April 1974, a peaceful "
                "military coup that ended the Estado Novo dictatorship and led to "
                "democracy in Portugal."
            ),
        },
        "Labor Day": {
            "subject": "Labour Day (Dia do Trabalhador)",
            "description": "International Workers' Day, celebrating workers' rights.",
        },
        "Corpus Christi": {
            "subject": "Corpus Christi (Corpo de Deus)",
            "description": (
                "Catholic feast honouring the Eucharist. Marked by religious "
                "processions through Portuguese towns and cities."
            ),
        },
        "Portugal Day": {
            "subject": "Portugal Day (Dia de Portugal, de Camões e das Comunidades)",
            "description": (
                "National day commemorating the death of poet Luís de Camões in 1580, "
                "author of Os Lusíadas. Honours Portugal, its culture and the global "
                "Portuguese diaspora."
            ),
        },
        "Assumption Day": {
            "subject": "Assumption of Mary (Assunção de Nossa Senhora)",
            "description": ("Catholic feast celebrating the bodily assumption of the Virgin Mary into heaven."),
        },
        "Republic Day": {
            "subject": "Republic Day (Implantação da República)",
            "description": (
                "Commemorates the 5 October 1910 revolution that overthrew the Portuguese "
                "monarchy and established the First Portuguese Republic."
            ),
        },
        "All Saints' Day": {
            "subject": "All Saints' Day (Dia de Todos os Santos)",
            "description": (
                "Catholic feast honouring all saints. Families traditionally visit "
                "cemeteries to remember deceased relatives."
            ),
        },
        "Restoration of Independence": {
            "subject": "Restoration of Independence Day (Restauração da Independência)",
            "description": (
                "Marks the 1 December 1640 uprising that ended sixty years of Iberian "
                "Union with Spain and restored Portuguese independence under the House "
                "of Braganza."
            ),
        },
        "Immaculate Conception": {
            "subject": "Immaculate Conception (Imaculada Conceição)",
            "description": (
                "Catholic feast celebrating the conception of the Virgin Mary free of "
                "original sin. Our Lady of the Immaculate Conception is the patron "
                "saint of Portugal."
            ),
        },
        "Christmas Day": {
            "subject": "Christmas Day (Natal)",
            "description": (
                "Christian feast celebrating the birth of Jesus Christ. Portuguese "
                "families traditionally gather for a Christmas Eve supper of bacalhau "
                "(salt cod) and exchange gifts at midnight."
            ),
        },
    },
    "EN": {
        "New Year's Day": {
            "subject": "New Year's Day",
            "description": "Celebration of the start of the new calendar year.",
        },
        "Good Friday": {
            "subject": "Good Friday",
            "description": ("Christian holy day commemorating the crucifixion of Jesus Christ."),
        },
        "Easter Monday": {
            "subject": "Easter Monday",
            "description": ("The day after Easter Sunday, traditionally a day of rest following Easter celebrations."),
        },
        "May Day": {
            "subject": "Early May Bank Holiday",
            "description": (
                "Bank holiday on the first Monday of May, with roots in ancient "
                "spring festivals and the modern labour movement."
            ),
        },
        "Spring Bank Holiday": {
            "subject": "Spring Bank Holiday",
            "description": ("Bank holiday on the last Monday of May. Replaced the moveable Whit Monday in 1971."),
        },
        "Late Summer Bank Holiday": {
            "subject": "Summer Bank Holiday",
            "description": (
                "Bank holiday on the last Monday of August, marking the unofficial end of summer in England."
            ),
        },
        "Christmas Day": {
            "subject": "Christmas Day",
            "description": "Christian feast celebrating the birth of Jesus Christ.",
        },
        "Boxing Day": {
            "subject": "Boxing Day",
            "description": (
                "Day after Christmas, originally when servants and tradespeople "
                "received gift boxes from employers and customers."
            ),
        },
    },
}


# International holidays. Fixed-date global observances used everywhere.
# Format: (month, day, name, subject, description)
INTERNATIONAL_HOLIDAYS: list[tuple[int, int, str, str, str]] = [
    (
        1,
        1,
        "New Year's Day",
        "New Year's Day",
        "Global celebration marking the first day of the Gregorian calendar year.",
    ),
    (
        2,
        14,
        "Valentine's Day",
        "Saint Valentine's Day",
        "Day celebrating romantic love, named after the Christian martyr Saint Valentine.",
    ),
    (
        3,
        8,
        "International Women's Day",
        "International Women's Day",
        "United Nations day celebrating women's rights, achievements and the ongoing "
        "fight for gender equality. Originated in the early 20th century labour movement.",
    ),
    (
        4,
        22,
        "Earth Day",
        "Earth Day",
        "Annual event demonstrating support for environmental protection, first held on 22 April 1970.",
    ),
    (
        5,
        1,
        "International Workers' Day",
        "International Workers' Day / Labour Day",
        "Worldwide celebration of the labour movement, commemorating the 1886 Haymarket affair in Chicago.",
    ),
    (
        6,
        5,
        "World Environment Day",
        "World Environment Day",
        "United Nations day for encouraging awareness and action to protect the environment.",
    ),
    (
        9,
        21,
        "International Day of Peace",
        "International Day of Peace",
        "United Nations day devoted to strengthening the ideals of peace, observed by "
        "a global ceasefire and non-violence.",
    ),
    (
        10,
        5,
        "World Teachers' Day",
        "World Teachers' Day",
        "UNESCO day celebrating the role of teachers in providing quality education.",
    ),
    (
        12,
        10,
        "Human Rights Day",
        "Human Rights Day",
        "Marks the adoption of the Universal Declaration of Human Rights by the UN General Assembly in 1948.",
    ),
    (
        12,
        25,
        "Christmas Day",
        "Christmas Day",
        "Christian feast celebrating the birth of Jesus Christ, observed as a public holiday in much of the world.",
    ),
]
