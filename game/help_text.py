"""The rules as the '?' screen shows them, in English and Russian (the rules only: nothing on how to solve a case,
beyond the hints of the original's own rules). The markup is read by help_view.py (see there): chapters '#! ' (about), '# ',
'#+ ' (a game) and '## ' (the quick reference), '### ' subheadings, '- ' and '1. ' items, '> ' notes, **bold**,
[KEY]; '@questions' and '@cards' are the tables."""

# the help's own title, and the groups of its contents: about the game (no title), the rules, the games, the quick reference
CONTENTS = {'en': ('Help', '', 'Rules', 'Games', 'Quick reference'), 'ru': ('Справка', '', 'Правила', 'Режимы игры', 'Справочник')}

QUESTIONS_EN = [
    '1  Did the murderer go to the East Side?',
    '2  Did a MALE do it?',
    '3  What area did the murderer go to?  3 / 4 / 5',
    '4  Was the murder weapon a .38?',
    '5  Where was the .38 hidden?  A-F',
    '6  Where was the .45 hidden?  A-F',
    '7  Which place had only 3 suspects?  A-F',
    '8  Did the murderer go to A, B or C?',
    '9  Were you on the East Side?',
    '10  What area were you in?  3 / 4 / 5',
    '11  Were you at A, B or C?',
    '12  Were you where a weapon was hidden?',
    "13  Are an odd-numbered suspect's prints on the .38?",
    "14  Are an odd-numbered suspect's prints on the .45?",
]
QUESTIONS_RU = [
    '1  Убийца скрылся на East Side?',
    '2  Убийца - мужчина?',
    '3  В какой район скрылся убийца?  3 / 4 / 5',
    '4  Орудие убийства - .38?',
    '5  Где спрятан .38?  A-F',
    '6  Где спрятан .45?  A-F',
    '7  В каком месте было только 3 подозреваемых?  A-F',
    '8  Убийца скрылся в A, B или C?',
    '9  Ты был на East Side?',
    '10  В каком районе ты был?  3 / 4 / 5',
    '11  Ты был в A, B или C?',
    '12  Ты был там, где спрятано оружие?',
    '13  Отпечатки на .38 - нечётного подозреваемого?',
    '14  Отпечатки на .45 - нечётного подозреваемого?',
]

HELP = {
    'en': [
        '#! About the game',
        '**Electronic Detective** is a deduction game by Ideal (1979): an electronic machine with a keypad and a '
        'seven-digit display, twenty suspect cards and Case Fact Sheets. A murder has been committed; the other 19 '
        'people have scattered to six places around town. The players question them in turns, collect alibis and '
        'private answers, and name the murderer.',
        '### This version',
        'A fan project: the game on a PC or a phone.',
        '- **Our machine** (the default) - the behaviour of the device: the same keys, display, sounds, questions and '
        'answers, compared key by key with the original program; but the cases are dealt fairly at random, and every '
        'case has a number.',
        '- **The original** - the real program (ROM) run by an emulator of its TMS0980 chip. The ROM is not included.',
        '- New games, the par (the turns a methodical detective needs), records, and a board game to print.',
        '> Not affiliated with or endorsed by Ideal or the present owners of the game. The suspect cards are not '
        'included: use the original ones or your own copy (who answers what is in the quick reference).',

        '# Starting a game',
        'Switch on with [ON]. Hold a digit while pressing [ON] to choose the game or a service:',
        '- [ON] - the usual game, dealt fairly (without the patterns of the original).',
        '- [1] + [ON] - the original (needs its ROM; not on the phone).',
        '- [2] + [ON] - Two False Alibis, [3] + [ON] - the Accomplice, [4] + [ON] - Everybody Lies.',
        '- [9] + [ON] - a case by its number.',
        '- [8] + [ON] - cases for the board game (PC only).',
        '- [0] + [ON] - clear the records and the running score.',
        '### Level and players',
        'Type the level and the number of players (1-4), then [ENTER]. The display shows the number of the victim '
        'and the place of the body.',
        '- **1** Master Detective - one private question a turn.',
        '- **2** Sleuth - up to two.',
        '- **3** Gumshoe - up to three.',
        'Everybody Lies has levels 2 and 3 only.',
        '### A case by its number',
        '[9] + [ON], a number from 1 to 9999999, [ENTER]. The machine remembers it and goes dark; the next game you '
        'start plays that case ([OFF] before that forgets it).',
        'The same number is the same case on any device: give it to a friend, or play the date as the case of the '
        'day. Every case shows its number at the start and in the summary. A case chosen by number does not go to '
        'the records.',
        '### Other',
        '[0] + [ON] asks first: [ENTER] clears the records, any other key keeps them.',
        'The speaker at the top right of the message field turns the sound off and on (on a PC also the M key).',

        '# A turn',
        'One suspect is questioned per turn.',
        '### Alibi - everybody hears it',
        '[SUSPECT], number, [ENTER]. The display reads: side, area, place, companion, companion. An alibi holds one '
        'to three of these facts; an empty position means the suspect did not say.',
        '### Private question - for your eyes only',
        '[PRIVATE QUESTION], number, [ENTER]. Only questions from this suspect\'s card, no more per turn than the '
        'level (fewer is fine).',
        'Answers: YES, NO, an area 3-5, a place A-F, or 00 000 00 - "I don\'t know".',
        '### Ending the turn',
        '[END TURN] passes the turn. A suspect may be questioned again later; the victim cannot be questioned.',
        '- **EE** - a wrong entry, or a question that is not on the card.',
        '- **END** - no questions are left this turn.',

        '# Accusing',
        'At the start of your turn, before choosing a suspect: [I ACCUSE], number, [ENTER]. One accusation per game.',
        '- **Right** - you win.',
        '- **Wrong** - the machine shows the murderer and you are out; the other players go on.',

        '# The town',
        '### Places',
        '**A** Art Show, **B** Theatre, **C** Card Party, **D** Docks, **E** Embassy, **F** Factory.',
        '### Addresses',
        'Each place is on a side - **1** West, **2** East - and in an area - **3** Uptown, **4** Midtown, '
        '**5** Downtown.',
        '### Guns and people',
        'Two guns, a .38 and a .45; one of them is the murder weapon.',
        'Suspects 1-10 are men, 11-20 are women.',

        '# What the machine guarantees',
        '1. Suspects tell the truth - with one exception (4).',
        '2. Four places hold four suspects each: an even and an odd man, an even and an odd woman.',
        '3. The fifth place holds three. The sixth is the place of the body: nobody is there, and no gun.',
        '4. The prints on the murder weapon: whether they are an odd suspect\'s is told reliably only by a suspect '
        'of the murderer\'s sex at the place of that weapon. Others at a gun may lie about the prints, or may not. '
        'Where there is no gun, 13 and 14 are answered "I don\'t know".',
        '5. The murderer is never at the place of the body, nor where either gun lies.',

        '# How to solve a case',
        'You need all the facts of the murder: only one suspect fits them.',
        '- **Sex** of the murderer - question 2.',
        '- **Weapon** (.38 or .45) - question 4.',
        '- **Where the weapon lies** - question 5 or 6.',
        '- **Odd or even prints** - 13 or 14 to a suspect of the murderer\'s sex from the place of the weapon.',
        '- **Where the murderer could not go** - the place of the body and of both guns; A-C if somebody answered '
        'NO to 8, D-F if YES.',
        '- **Where the murderer is** - alibis; 1 and 3 (about the murderer), 9 and 10 (about the one questioned).',
        '> **By elimination.** If the murderer is an odd man and every odd man but one is, by the alibis, where the '
        'murderer cannot be, the one left is the murderer.',
        '### The fact sheet',
        '1 - the facts of the murder; 2 - who was where (places, addresses, guns); 3 - scratch notes; 4 - your answer.',

        '# Board game (8 + ON, PC only)',
        'To play without the machine, from printed sheets.',
        '1. Hold [8], press [ON], type how many cases to write (1-10), [ENTER]: the machine goes dark.',
        '2. Choose the game: [ON] the usual one, [2] + [ON], [3] + [ON] or [4] + [ON] the others. [OFF] cancels.',
        '3. The file cases_<date>_<time>.html appears beside the program (if its folder is read-only: in the '
        'ElectronicDetective folder of AppData or ~/.config). Open it in a browser, print on A4 without headers and '
        'footers.',
        '### The sheets',
        '- **For all cases:** the rules of this game, and how to read the display.',
        '- **For each case:** an index (suspect and question - a paragraph number) and the answers (the paragraphs, '
        'and the par of each level at the bottom); some games add a sheet - the accusation of a pair, or notes.',
        'Read only the paragraph you asked for. The sheets are in the language of this help. The number of the case '
        'is on its sheets: it can be played on the machine too ([9] + [ON]).',

        '#+ The original (1 + ON)',
        'The real program of the 1979 device, run instruction by instruction by an emulator of its TMS0980 chip.',
        '- It needs the ROM of the original: on the first [1] + [ON] the program asks where it is. Not on the phone.',
        '- The case depends on when you press [ENTER] at the start and how long you hold it: up to about 0.8 s, then '
        'the machine goes on by itself.',
        '- Its cases have no numbers: a case by number ([9] + [ON]) and the board game are for our machine only.',
        '- The display is drawn by how long each segment was really lit, as on the device.',
        '> The rules are those of the usual game. But the deals of the original are not quite random - they have '
        'patterns; our machine deals fairly.',

        '#+ Two False Alibis (2 + ON)',
        'Everything as in the usual game, except:',
        '1. Two suspects lie in their alibi: the murderer, and one more with something else to hide. Each repeats the '
        'alibi of another suspect of the same sex and parity, who was at another place.',
        '2. Private questions are answered as always - by these two as well. So an alibi can be tested by a question '
        'about the place (9-11), or by the word of those who were there.',
        '3. Nobody claims to have been where a gun lies.',
        '> Catching a liar is not yet finding the murderer: there are two liars. Every case can be solved by reasoning.',

        '#+ The Accomplice (3 + ON)',
        'Everything as in the usual game, except:',
        '1. The murderer has an accomplice, and the two keep to one false story: to the questions about the murderer '
        '(1, 2, 3, 8) both answer as if another suspect, an innocent one, had done it.',
        '2. Their alibis are true, and so are their other answers. Everybody else tells the truth.',
        '3. Name both: [I ACCUSE], the murderer, [ENTER] - the display shows it with -- ; then the accomplice, '
        '[ENTER]. YES only if both are right, in this order; NO does not say which is wrong, and the player is out.',
        '> Every case can be solved by reasoning, the pair included. In the board game the pair is accused on the '
        'last sheet of the case: a grid of murderer and accomplice.',

        '#+ Everybody Lies (4 + ON)',
        'Everything as in the usual game, except:',
        '1. Every alibi is false - everybody\'s, the murderer\'s too - in every field it shows: not that side, not '
        'that area, not that place (never the place of the body).',
        '2. Each companion named was somewhere else; the true companion is another suspect of the same sex and parity.',
        '3. Which fields an alibi shows is as in the usual game.',
        '4. Private questions are answered truly; the prints work as usual.',
        '5. Levels 2 and 3 only.',
        '> **An alibi says NOT, an answer says YES.** Every case can be solved by reasoning; a methodical detective '
        'needs at most 20 turns on level 2.',
        '### Example',
        'No. 4 says: side 1, the Card Party, with No. 15. Read it: 4 was on the East Side, not at the Card Party; 15 '
        'was not where 4 was.',
        '### Count the kinds',
        'A place of four holds one suspect of each kind (sex and parity), so the place of three has nobody of the '
        'victim\'s kind. When a suspect has one place left, it is closed to the others of their kind.',
        '### Suppose and check',
        'Say No. 10 can only be at A or F, and of the odd men only No. 5 can still be at F. 10 named 5 as a companion, '
        'so they were apart: were 10 at F, F would have no odd man. So 10 was at A.',
        'In the board game the last sheet of every case, Notes, has grids for crossing out.',

        '## Private questions',
        '@questions',
        'Questions 13 and 14 can be put to everybody; the others are on the cards.',

        '## The cards: who can be asked what',
        'After an alibi the message field lists the questions of that suspect.',
        '@cards',
    ],
    'ru': [
        '#! Об игре',
        '**Electronic Detective** - детективная игра фирмы Ideal (1979): электронная машина с клавиатурой и '
        'семиразрядным табло, двадцать карточек подозреваемых и листы записей. Совершено убийство; остальные 19 '
        'человек разъехались по шести местам города. Игроки по очереди допрашивают их, собирают алиби и частные '
        'ответы и называют убийцу.',
        '### Эта версия',
        'Любительский проект: игра на ПК и телефоне.',
        '- **Наша машина** (по умолчанию) - повторяет поведение устройства: те же клавиши, табло, звуки, вопросы и '
        'ответы, сверенные с программой оригинала клавиша за клавишей; но дела раздаются честно и случайно, и у '
        'каждого дела есть номер.',
        '- **Оригинал** - настоящая программа (ROM) на эмуляторе её микросхемы TMS0980. ROM не входит в комплект.',
        '- Новые режимы, пар (сколько ходов нужно методичному сыщику), рекорды и настольная игра для печати.',
        '> Проект не связан с Ideal и нынешними владельцами игры и не одобрен ими. Карточки подозреваемых не входят '
        'в комплект: нужны оригинальные или своя копия (кто на какие вопросы отвечает - в «Справочнике»).',

        '# Начало игры',
        'Включение - [ON]. Удерживайте цифру, нажимая [ON], чтобы выбрать игру или действие:',
        '- [ON] - обычная игра с честной раздачей (без закономерностей оригинала).',
        '- [1] + [ON] - оригинал (нужен его ROM; на телефоне нет).',
        '- [2] + [ON] - «Два ложных алиби», [3] + [ON] - «Сообщник», [4] + [ON] - «Все врут».',
        '- [9] + [ON] - дело по номеру.',
        '- [8] + [ON] - дела для настольной игры (только ПК).',
        '- [0] + [ON] - стереть рекорды и накопленный счёт.',
        '### Уровень и игроки',
        'Введите уровень и число игроков (1-4), затем [ENTER]. На табло - номер жертвы и место тела.',
        '- **1** Master Detective - один частный вопрос за ход.',
        '- **2** Sleuth - до двух.',
        '- **3** Gumshoe - до трёх.',
        'В «Все врут» - только уровни 2 и 3.',
        '### Дело по номеру',
        '[9] + [ON], номер от 1 до 9999999, [ENTER]. Машина запомнит его и погаснет; следующая игра, которую вы '
        'начнёте, будет этим делом ([OFF] до этого - забыть номер).',
        'Один номер - одно и то же дело на любом устройстве: продиктуйте его другу или играйте дату как дело дня. '
        'Номер показан в начале и в итоге. Дело по номеру в рекорды не идёт.',
        '### Прочее',
        '[0] + [ON] сначала спрашивает: [ENTER] стирает рекорды, любая другая клавиша оставляет.',
        'Динамик в правом верхнем углу поля сообщений выключает и включает звук (на ПК ещё клавиша M).',

        '# Ход',
        'За ход допрашивается один подозреваемый.',
        '### Алиби - слышат все',
        '[SUSPECT], номер, [ENTER]. Табло читается так: сторона, район, место, спутник, спутник. В алиби от одного '
        'до трёх таких фактов; пустая позиция - об этом подозреваемый не сказал.',
        '### Частный вопрос - только для ваших глаз',
        '[PRIVATE QUESTION], номер, [ENTER]. Только вопросы с карточки подозреваемого, за ход не больше, чем '
        'разрешает уровень (можно меньше).',
        'Ответы: YES, NO, район 3-5, место A-F или 00 000 00 - «не знаю».',
        '### Конец хода',
        '[END TURN] передаёт ход. Подозреваемого можно допросить снова позже; жертву допросить нельзя.',
        '- **EE** - неверный ввод или вопрос не с карточки.',
        '- **END** - вопросы на этот ход кончились.',

        '# Обвинение',
        'В начале хода, до выбора подозреваемого: [I ACCUSE], номер, [ENTER]. Одно обвинение на игру.',
        '- **Верно** - вы победили.',
        '- **Неверно** - машина показывает убийцу, вы выбываете; остальные играют дальше.',

        '# Город',
        '### Места',
        '**A** Art Show, **B** Theatre, **C** Card Party, **D** Docks, **E** Embassy, **F** Factory.',
        '### Адреса',
        'У каждого места есть сторона - **1** West, **2** East - и район - **3** Uptown, **4** Midtown, '
        '**5** Downtown.',
        '### Оружие и люди',
        'Два пистолета, .38 и .45; один из них - орудие убийства.',
        'Подозреваемые 1-10 - мужчины, 11-20 - женщины.',

        '# Что машина гарантирует',
        '1. Подозреваемые говорят правду - с одним исключением (4).',
        '2. В четырёх местах по четыре подозреваемых: чётный и нечётный мужчина, чётная и нечётная женщина.',
        '3. В пятом месте трое. Шестое - место тела: там нет ни людей, ни оружия.',
        '4. Отпечатки на орудии убийства: нечётного ли они подозреваемого, надёжно сообщает только подозреваемый того '
        'же пола, что убийца, из места, где лежит это орудие. Остальные у оружия могут солгать про отпечатки, а могут '
        'и нет. Там, где оружия нет, на 13 и 14 отвечают «не знаю».',
        '5. Убийцы никогда нет на месте тела и там, где лежит любой из пистолетов.',

        '# Как раскрыть дело',
        'Нужно знать все факты убийства: им соответствует только один подозреваемый.',
        '- **Пол** убийцы - вопрос 2.',
        '- **Орудие** (.38 или .45) - вопрос 4.',
        '- **Где лежит орудие** - вопрос 5 или 6.',
        '- **Чётность отпечатков** - 13 или 14 подозреваемому того же пола, что убийца, из места, где лежит орудие.',
        '- **Куда убийца не мог скрыться** - место тела и места обоих пистолетов; A-C, если кто-то ответил NO на 8, '
        'D-F, если YES.',
        '- **Где убийца** - алиби; 1 и 3 (про убийцу), 9 и 10 (про допрашиваемого).',
        '> **От противного.** Если убийца - нечётный мужчина, а все нечётные мужчины, кроме одного, по алиби там, где '
        'убийцы быть не может, - оставшийся и есть убийца.',
        '### Лист записей',
        '1 - факты убийства; 2 - кто где (места, адреса, оружие); 3 - черновик; 4 - ваш ответ.',

        '# Настольная игра (8 + ON, только ПК)',
        'Чтобы играть без машины, по распечатанным листам.',
        '1. Удерживая [8], нажмите [ON], введите, сколько дел записать (1-10), [ENTER]: машина погаснет.',
        '2. Выберите игру: [ON] - обычная, [2] + [ON], [3] + [ON] или [4] + [ON] - остальные. [OFF] отменяет.',
        '3. Файл cases_<дата>_<время>.html появится рядом с программой (если туда нельзя писать - в папке '
        'ElectronicDetective в AppData или ~/.config). Откройте его в браузере и напечатайте на A4 без колонтитулов.',
        '### Листы',
        '- **На все дела:** правила этой игры и как читать табло.',
        '- **На каждое дело:** указатель (подозреваемый и вопрос - номер параграфа) и ответы (параграфы, внизу - пар '
        'для каждого уровня); в некоторых играх ещё лист - обвинение пары или записи.',
        'Читайте только тот параграф, о котором спросили. Листы пишутся на языке этой справки. Номер дела стоит на '
        'его листах: то же дело можно сыграть на машине ([9] + [ON]).',

        '#+ Оригинал (1 + ON)',
        'Настоящая программа устройства 1979 года, выполняемая команда за командой эмулятором микросхемы TMS0980.',
        '- Нужен ROM оригинала: при первом [1] + [ON] программа спросит, где он. На телефоне этого режима нет.',
        '- Дело зависит от того, когда вы нажмёте [ENTER] в начале игры и сколько продержите: до 0,8 с, дальше '
        'машина продолжает сама.',
        '- У дел нет номеров: дело по номеру ([9] + [ON]) и настольная игра - только для нашей машины.',
        '- Табло рисуется по тому, сколько на самом деле горел каждый сегмент, - как на устройстве.',
        '> Правила - как в обычной игре. Но раздача оригинала не вполне случайна, в ней есть закономерности; наша '
        'машина раздаёт дела честно.',

        '#+ Два ложных алиби (2 + ON)',
        'Всё как в обычной игре, кроме следующего:',
        '1. Двое лгут в алиби: убийца и ещё один, которому есть что скрывать. Каждый повторяет алиби другого '
        'подозреваемого того же пола и чётности, который был в другом месте.',
        '2. На частные вопросы все отвечают как всегда - и эти двое тоже. Поэтому алиби можно проверить вопросом о '
        'месте (9-11) или показаниями тех, кто там был.',
        '3. Никто не говорит, что был там, где лежит оружие.',
        '> Поймать лжеца - ещё не значит найти убийцу: лжецов двое. Каждое дело можно раскрыть рассуждением.',

        '#+ Сообщник (3 + ON)',
        'Всё как в обычной игре, кроме следующего:',
        '1. У убийцы есть сообщник, и они держатся одной ложной версии: на вопросы об убийце (1, 2, 3, 8) оба '
        'отвечают так, будто это сделал другой подозреваемый, невиновный.',
        '2. Их алиби правдивы, остальные их ответы тоже. Все прочие говорят правду.',
        '3. Назовите обоих: [I ACCUSE], номер убийцы, [ENTER] - на табло он и -- ; затем номер сообщника, [ENTER]. '
        'YES - только если верны оба и в этом порядке; NO не говорит, кто назван неверно, и игрок выбывает.',
        '> Каждое дело можно раскрыть рассуждением, вместе с парой. В настольной игре пару обвиняют на последнем '
        'листе дела: в сетке «убийца × сообщник».',

        '#+ Все врут (4 + ON)',
        'Всё как в обычной игре, кроме следующего:',
        '1. Все алиби ложны - у всех, и у убийцы тоже, - в каждом показанном поле: не та сторона, не тот район, не то '
        'место (и никогда не место тела).',
        '2. Каждый названный спутник был в другом месте; настоящий спутник - другой подозреваемый того же пола и '
        'чётности.',
        '3. Какие поля есть в алиби - как в обычной игре.',
        '4. На частные вопросы все отвечают правду; отпечатки - как обычно.',
        '5. Только уровни 2 и 3.',
        '> **Алиби говорит НЕ, ответ говорит ДА.** Каждое дело можно раскрыть рассуждением; методичному сыщику на '
        'уровне 2 хватает 20 ходов.',
        '### Пример',
        '№ 4 говорит: сторона 1, Card Party, с № 15. Читаем: 4 был на East Side, не в Card Party; 15 был не там, где 4.',
        '### Считайте роды',
        'В месте на четверых - по одному каждого рода (пол и чётность), поэтому в месте на троих нет рода жертвы. '
        'Если у подозреваемого осталось одно место, оно закрыто для остальных его рода.',
        '### Предположите и проверьте',
        'Пусть № 10 может быть только в A или F, а из нечётных мужчин в F может быть только № 5. 10 назвал 5 '
        'спутником, значит, они были порознь: будь 10 в F, в F не нашлось бы нечётного мужчины. Значит, 10 был в A.',
        'В настольной игре на последнем листе каждого дела, «Записи», - сетки для вычёркивания.',

        '## Частные вопросы',
        '@questions',
        'Вопросы 13 и 14 можно задать всем; остальные - по карточкам.',

        '## Карточки: кому какие вопросы',
        'После алиби в поле сообщений перечислены вопросы этого подозреваемого.',
        '@cards',
    ],
}
