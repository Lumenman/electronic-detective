"""The rules as the '?' screen shows them, in English and Russian (the rules only: nothing on how to solve a case).
A line starting with '# ' is a heading; an empty string is a gap. The window wraps the lines and cuts them into pages."""

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
        '# Starting a game',
        'ON - a game dealt fairly, without the patterns of the original.',
        'Hold 1 and press ON - the original (needs its ROM; not on the phone).',
        'Hold 2 and press ON - the game of Two False Alibis (see the last section).',
        'Hold 9 and press ON - choose a case by its number: type a number from 1 to 9999999 and press ENTER. The '
        'machine remembers it and goes dark; the next game you start (ON, or 2 + ON) plays that case '
        '(OFF before that forgets the number). '
        'The same number is the same case on any device: give it to a friend, or agree to play the date as the case '
        'of the day. Every case shows its number at the start and in the final summary. A case chosen by its number '
        'does not go to the records or the running score.',
        'Hold 8 and press ON (PC only) - write cases to print and play on paper (see "Cases on paper").',
        'Hold 0 and press ON - clear the records and the running score: ENTER confirms, any other key keeps them.',
        'The speaker at the top right of the message field turns the sound off and on (on a PC also the M key).',
        '',
        'Then enter the level (1 Master Detective, 2 Sleuth, 3 Gumshoe: that many private questions per turn), '
        'the number of players (1-4) and ENTER. The display shows the number of the victim and the place of the body.',
        '',
        '# A turn',
        'One suspect is questioned per turn.',
        'Alibi (everybody hears it): SUSPECT, number, ENTER. The display reads: side, area, place, companion, companion. '
        'An alibi holds one to three of these facts; an empty position means the suspect did not say.',
        'Private question (for your eyes only): PRIVATE QUESTION, number, ENTER. Only questions from the card of this '
        'suspect, no more per turn than the level. Answers: YES, NO, an area 3-5, a place A-F, or 00 000 00 for '
        "'I don't know'.",
        'END TURN passes the turn. A suspect may be questioned again later. The victim cannot be questioned.',
        'EE means a wrong entry or a question that is not on the card. END means no questions are left this turn.',
        '',
        '# Accusing',
        'At the start of your turn, before choosing a suspect: I ACCUSE, number, ENTER. One accusation per game.',
        'Right - you win. Wrong - the machine shows the murderer and you are out; other players go on.',
        '',
        '# The town',
        'Six places: A Art Show, B Theatre, C Card Party, D Docks, E Embassy, F Factory.',
        'Each place is on a side (1 West, 2 East) and in an area (3 Uptown, 4 Midtown, 5 Downtown).',
        'There are two guns, a .38 and a .45; one of them is the murder weapon.',
        'Suspects 1-10 are men, 11-20 are women.',
        '',
        '# Private questions',
        *QUESTIONS_EN,
        'Questions 13 and 14 can be put to everybody; the others are on the cards.',
        '',
        '# The cards: who can be asked what',
        'After an alibi the message field lists the questions of that suspect.',
        '@cards',
        '',
        '# What the machine guarantees',
        '1. Suspects tell the truth - with one exception (4).',
        '2. Four places hold four suspects each: an even and an odd man, an even and an odd woman.',
        '3. The fifth place holds three suspects. The sixth is the place of the body: nobody is there, and no gun.',
        '4. Fingerprints on the murder weapon: whether they belong to an odd or an even suspect is told reliably only '
        "by a suspect of the murderer's sex who went where that weapon lies. Others at a weapon may lie about the "
        "prints, or may not. Where there is no gun the answer to 13 and 14 is 'I don't know'.",
        '5. The murderer is never at the place of the body, nor where either gun lies.',
        '',
        '# How to solve a case',
        'You need all the facts of the murder (section 1 of the fact sheet): only one suspect fits them.',
        'Sex of the murderer - question 2.',
        'The weapon (.38 or .45) - question 4.',
        'Where the weapon lies - question 5 or 6.',
        "Odd or even prints on the weapon - question 13 or 14 to a suspect of the murderer's sex from the place "
        'where the weapon lies.',
        'Where the murderer could not go - the place of the body; the places of both guns; A-C if somebody answered '
        'NO to question 8, D-F if YES.',
        'Where the murderer is - alibis; questions 1 and 3 (about the murderer), 9 and 10 (about the one questioned).',
        'You can also go by elimination: if the murderer is an odd man and every odd man but one is, by the alibis, '
        'where the murderer cannot be, the one left is the murderer.',
        'The fact sheet: section 1 - the facts of the murder; 2 - who was where (places, addresses, guns); '
        '3 - scratch notes (who said what); 4 - your answer.',
        '',
        '# Cases on paper (8 + ON, PC only)',
        'To play without the machine. Hold 8 and press ON, type how many cases to write (1-50) and press ENTER: the '
        'machine goes dark. Then ON writes that many random cases of the usual game, and 2 + ON of Two False Alibis; '
        'OFF cancels. Nothing of the cases is shown on the screen.',
        'The file cases_<date>_<time>.html appears beside the program. Open it in a browser and print it on A4, without headers and '
        'footers. First come two sheets for all cases: how to read the display, and the rules in brief. Then two '
        'sheets per case: an index (suspect and question - the number of a paragraph) and the answers (the numbered '
        'paragraphs, each as the display shows it, and at the bottom the par of each level). Read only the paragraph '
        'you asked for. The par takes a few seconds per case to count.',
        'The sheets are written in the language of this help: switch it with the button below before writing.',
        'The number of the case is on its sheets: the same case can be played on the machine (9 + ON).',
        '',
        '# Two False Alibis (2 + ON)',
        'Everything as above, except:',
        '1. Two suspects lie in their alibi: the murderer, and one more who has something else to hide. Each of them '
        "simply repeats somebody else's alibi: that of another suspect of the same sex and parity, who was at a "
        'different place.',
        '2. Private questions are answered as always - by these two as well. So an alibi can be tested by a question '
        'about the place (9-11) to the same suspect, or by the word of those who were there.',
        '3. Nobody claims to have been where a gun lies.',
        'Catching a liar is not yet finding the murderer: there are two liars. Every case can be solved by reasoning.',
    ],
    'ru': [
        '# Начало игры',
        'ON - игра с честной раздачей, без закономерностей оригинала.',
        'Удерживая 1, нажмите ON - оригинал (нужен его ROM; на телефоне нет).',
        'Удерживая 2, нажмите ON - игра «Два ложных алиби» (см. последний раздел).',
        'Удерживая 9, нажмите ON - выбор дела по номеру: введите номер от 1 до 9999999 и нажмите ENTER. Машина '
        'запомнит его и погаснет; следующая игра, которую вы начнёте (ON или 2 + ON), будет этим делом '
        '(OFF до этого - забыть номер). Один номер - '
        'одно и то же дело на любом устройстве: продиктуйте его другу или договоритесь играть дату как дело дня. '
        'Номер каждого дела показан в начале и в итоге. Дело, выбранное по номеру, в рекорды и накопленный счёт '
        'не идёт.',
        'Удерживая 8, нажмите ON (только ПК) - записать дела для печати и игры на бумаге (см. «Дела на бумаге»).',
        'Удерживая 0, нажмите ON - стереть рекорды и накопленный счёт: ENTER подтверждает, любая другая клавиша '
        'оставляет их.',
        'Динамик в правом верхнем углу поля сообщений выключает и включает звук (на ПК ещё клавиша M).',
        '',
        'Затем введите уровень (1 Master Detective, 2 Sleuth, 3 Gumshoe: столько частных вопросов за ход), '
        'число игроков (1-4) и ENTER. На табло - номер жертвы и место тела.',
        '',
        '# Ход',
        'За ход допрашивается один подозреваемый.',
        'Алиби (слышат все): SUSPECT, номер, ENTER. Табло читается так: сторона, район, место, спутник, спутник. '
        'В алиби от одного до трёх таких фактов; пустая позиция - об этом подозреваемый не сказал.',
        'Частный вопрос (только для ваших глаз): PRIVATE QUESTION, номер, ENTER. Только вопросы с карточки этого '
        'подозреваемого, за ход не больше, чем разрешает уровень. Ответы: YES, NO, район 3-5, место A-F или '
        '00 000 00 - «не знаю».',
        'END TURN передаёт ход. Подозреваемого можно допросить снова позже. Жертву допросить нельзя.',
        'EE - неверный ввод или вопрос не с карточки. END - вопросы на этот ход кончились.',
        '',
        '# Обвинение',
        'В начале хода, до выбора подозреваемого: I ACCUSE, номер, ENTER. Одно обвинение на игру.',
        'Верно - вы победили. Неверно - машина показывает убийцу, вы выбываете; остальные играют дальше.',
        '',
        '# Город',
        'Шесть мест: A Art Show, B Theatre, C Card Party, D Docks, E Embassy, F Factory.',
        'У каждого места есть сторона (1 West, 2 East) и район (3 Uptown, 4 Midtown, 5 Downtown).',
        'В городе два пистолета, .38 и .45; один из них - орудие убийства.',
        'Подозреваемые 1-10 - мужчины, 11-20 - женщины.',
        '',
        '# Частные вопросы',
        *QUESTIONS_RU,
        'Вопросы 13 и 14 можно задать всем; остальные - по карточкам.',
        '',
        '# Карточки: кому какие вопросы',
        'После алиби в поле сообщений перечислены вопросы этого подозреваемого.',
        '@cards',
        '',
        '# Что машина гарантирует',
        '1. Подозреваемые говорят правду - с одним исключением (4).',
        '2. В четырёх местах по четыре подозреваемых: чётный и нечётный мужчина, чётная и нечётная женщина.',
        '3. В пятом месте трое. Шестое - место тела: там нет ни людей, ни оружия.',
        '4. Отпечатки на орудии убийства: чётному или нечётному подозреваемому они принадлежат, надёжно сообщает '
        'только подозреваемый того же пола, что убийца, скрывшийся туда, где лежит это орудие. Остальные у оружия '
        'могут солгать про отпечатки, а могут и нет. Там, где оружия нет, на вопросы 13 и 14 отвечают «не знаю».',
        '5. Убийцы никогда нет на месте тела и там, где лежит любой из пистолетов.',
        '',
        '# Как раскрыть дело',
        'Нужно знать все факты убийства (раздел 1 листа): им соответствует только один подозреваемый.',
        'Пол убийцы - вопрос 2.',
        'Орудие (.38 или .45) - вопрос 4.',
        'Где лежит орудие - вопрос 5 или 6.',
        'Чётность отпечатков на орудии - вопрос 13 или 14 подозреваемому того же пола, что убийца, из места, '
        'где лежит орудие.',
        'Куда убийца не мог скрыться - место тела; места обоих пистолетов; A-C, если кто-то ответил NO на вопрос 8, '
        'D-F, если YES.',
        'Где убийца - алиби; вопросы 1 и 3 (про убийцу), 9 и 10 (про допрашиваемого).',
        'Можно идти и от противного: если убийца - нечётный мужчина, а все нечётные мужчины, кроме одного, по алиби '
        'находятся там, где убийцы быть не может, - оставшийся и есть убийца.',
        'Лист записей: раздел 1 - факты убийства; 2 - кто где (места, адреса, оружие); 3 - черновик (кто что сказал); '
        '4 - ваш ответ.',
        '',
        '# Дела на бумаге (8 + ON, только ПК)',
        'Чтобы играть без машины. Удерживая 8, нажмите ON, введите, сколько дел записать (1-50), и нажмите ENTER: '
        'машина погаснет. Затем ON запишет столько случайных дел обычной игры, а 2 + ON - игры «Два ложных алиби»; '
        'OFF отменяет. На экран о делах ничего не выводится.',
        'Файл cases_<дата>_<время>.html появится рядом с программой. Откройте его в браузере и напечатайте на A4, без колонтитулов. Сначала '
        'идут два листа на все дела: как читать табло и краткие правила. Затем по два листа на дело: указатель '
        '(подозреваемый и вопрос - номер параграфа) и ответы (пронумерованные параграфы, каждый - как на табло). '
        'Внизу листа ответов - пар для каждого уровня. Читайте только тот параграф, о котором спросили. Пар считается '
        'несколько секунд на дело.',
        'Листы пишутся на языке этой справки: переключите его кнопкой внизу до записи.',
        'Номер дела стоит на его листах: то же дело можно сыграть на машине (9 + ON).',
        '',
        '# Два ложных алиби (2 + ON)',
        'Всё как выше, кроме следующего:',
        '1. Двое лгут в алиби: убийца и ещё один подозреваемый, которому есть что скрывать. Каждый из них просто '
        'повторяет чужое алиби: алиби другого подозреваемого того же пола и той же чётности, который был в другом '
        'месте.',
        '2. На частные вопросы все отвечают как всегда - и эти двое тоже. Поэтому алиби можно проверить вопросом '
        'о месте (9-11) тому же подозреваемому или показаниями тех, кто там был.',
        '3. Никто не говорит, что был там, где лежит оружие.',
        'Поймать лжеца - ещё не значит найти убийцу: лжецов двое. Каждое дело можно раскрыть рассуждением.',
    ],
}
