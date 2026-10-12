import random

from day1 import (
    InvalidOperationError,
)
from day3 import Bank, Client
from day4 import Transaction, TransactionQueue, TransactionProcessor
from day5 import AuditLog, RiskAnalyzer

random.seed(42)   

def section(title):
    print()
    print('=' * 75)
    print(f'  {title}')
    print('=' * 75)


def subsection(title):
    print()
    print(f' ==={title}=== ')

def balance_in_rub(account, rates):
    '''Перевести баланс счёта в RUB по курсам'''
    if account._currency not in rates:
        raise InvalidOperationError(f'Нет курса для валюты {account._currency}')
    return account._balance * rates[account._currency]

def client_balance_in_rub(client, bank, rates):
    '''Общий баланс клиента в RUB'''
    total = 0.0
    for acc_id in client.account_ids:
        acc = bank._get_account(acc_id)
        total += balance_in_rub(acc, rates)
    return total

def create_bank():
    '''Создание банка с клиентами и счетами.'''
    bank = Bank('Демо Банк')

    clients_data = [
        ('Иванов Иван Иванович',     30, 'ivanov@mail.ru',   '+79991000001', 'pass1'),
        ('Петров Пётр Петрович',      25, 'petrov@mail.ru',   '+79991000002', 'pass2'),
        ('Сидоров Сидор Сидорович',   35, 'sidorov@mail.ru',  '+79991000003', 'pass3'),
        ('Смирнова Анна Сергеевна',   28, 'smirnova@mail.ru', '+79991000004', 'pass4'),
        ('Кузнецов Олег Иванович',    40, 'kuznetsov@mail.ru', '+79991000005', 'pass5'),
        ('Попова Мария Алексеевна',   22, 'popova@mail.ru',   '+79991000006', 'pass6'),
    ]

    client_ids = []
    for name, age, email, phone, password in clients_data:
        c = Client(name, age, email, phone, password)
        client_ids.append(bank.add_client(c))

    # Счета
    accounts = {}

    # Иванов: basic + savings
    accounts['ivanov_basic']   = bank.open_account(client_ids[0], 'basic', balance=100000)
    accounts['ivanov_savings'] = bank.open_account(client_ids[0], 'savings',
                                                    balance=50000, min_balance=10000)
    # Иванов: USD 
    accounts['ivanov_usd'] = bank.open_account(
        client_ids[0], 'basic', balance=1000, currency='USD'
    )   

    # Петров: basic
    accounts['petrov_basic']   = bank.open_account(client_ids[1], 'basic', balance=50000)

    # Сидоров: premium + basic
    accounts['sidorov_premium'] = bank.open_account(client_ids[2], 'premium',
                                                     balance=500000,
                                                     overdraft_limit=100000,
                                                     operation_fee=100)
    accounts['sidorov_basic']   = bank.open_account(client_ids[2], 'basic', balance=100000)

    # Смирнова: savings + basic
    accounts['smirnova_savings'] = bank.open_account(client_ids[3], 'savings',
                                                      balance=200000, min_balance=50000)
    accounts['smirnova_basic']   = bank.open_account(client_ids[3], 'basic', balance=30000)

    # Кузнецов: premium + investment
    accounts['kuznetsov_premium'] = bank.open_account(client_ids[4], 'premium',
                                                       balance=1000000,
                                                       overdraft_limit=200000,
                                                       operation_fee=200)
    accounts['kuznetsov_invest'] = bank.open_account(client_ids[4], 'investment',
                                                      balance=200000,
                                                      portfolio={'stocks': 100000,
                                                                 'bonds': 50000,
                                                                 'etf': 50000})

    # Попова: basic
    accounts['popova_basic'] = bank.open_account(client_ids[5], 'basic', balance=10000)

    return bank, client_ids, accounts

def generate_transactions(bank, accounts):
    '''Сгенерировать 40 транзакций'''
    transactions = []
    acc_list = list(accounts.values())

    for i in range(40):
        kind = random.choices(
            ['normal', 'error', 'suspicious'],
            weights=[0.6, 0.2, 0.2],
        )[0]

        if kind == 'normal':
            t = _make_normal(acc_list)
        elif kind == 'error':
            t = _make_error(acc_list)
        else:
            t = _make_suspicious(acc_list)

        transactions.append(t)

    return transactions

def _make_normal(acc_list):
    '''Обычный перевод между случайными счетами'''
    sender = random.choice(acc_list)
    receiver = random.choice([a for a in acc_list if a is not sender])

    amount = random.randint(100, 5000)

    return Transaction(
        'transfer', amount, 'RUB',
        sender_id=sender.account_id,
        receiver_id=receiver.account_id,
    )

def _make_error(acc_list):
    '''Транзакция с ощибкой'''
    sender = random.choice(acc_list)
    receiver = random.choice([a for a in acc_list if a is not sender])

    amount = sender._balance + random.randint(10000, 100000) # делаем транзакцию > баланса

    return Transaction(
        'transfer', amount, 'RUB',
        sender_id=sender.account_id,
        receiver_id=receiver.account_id,
    )

def _make_suspicious(acc_list):
    '''Подозрительная (крупная сумма)'''
    sender = random.choice(acc_list)
    receiver = random.choice([a for a in acc_list if a is not sender])

    amount = random.randint(150000, 500000)

    return Transaction(
        'transfer', amount, 'RUB',
        sender_id=sender.account_id,
        receiver_id=receiver.account_id,
    )

def process_transactions(bank, transactions, audit, analyzer, processor):
    queue = TransactionQueue()
    for t in transactions:
        queue.add(t)

    results = {'completed': [], 'failed': [], 'blocked': []}

    while not queue.is_empty():
        t = queue.get_next()
        if t is None:
            break

        processor.execute(t)   

        if t.status == 'completed':
            results['completed'].append(t)
        elif t.status == 'failed':
            reason = t.failure_reason or ''
            if 'high risk' in reason:
                results['blocked'].append(t)
            else:
                results['failed'].append(t)

    return results

def show_client_scenario(bank, client_id, audit, rates):
    '''Показать сценарий для клиента.'''
    client = bank._get_client(client_id)

    subsection(f'Сценарий клиента: {client.full_name}')
    print(f'   ID:     {client.client_id}')
    print(f'   Возраст: {client.age}')
    print(f'   Статус: {client.status}')

    
    print(f'\n   Счета ({len(client.account_ids)}):')
    total = 0
    for acc_id in client.account_ids:
        acc = bank._get_account(acc_id)
        bal_rub = balance_in_rub(acc, rates)
        total += bal_rub
        print(f'      {acc.__class__.__name__:18s} '
              f'...{acc_id[-4:]}  '
              f'{acc._balance} {acc._currency} '
              f'({bal_rub} RUB)  '
              f'[{acc._status}]')
    print(f'   Итого: {total} RUB')

    
    events = audit.get_events(client_id=client_id)
    print(f'\n   События в аудите: {len(events)}')
    for ev in events[:5]:  
        print(f"     [{ev['level']}] {ev['event_type']} {ev['message']}")

    # Подозрительные
    suspicious = [ev for ev in events
                  if ev['level'] in ('warning', 'error')]
    print(f'\n   Подозрительных: {len(suspicious)}')
    for ev in suspicious[:3]:
        print(f"{ev['message']}")

def show_reports(bank, audit, results, rates):
    '''Финальные отчёты'''

    subsection('Топ-3 клиента по балансу в RUB')
    ranking = []
    for client in bank._clients.values():
        total_rub = client_balance_in_rub(client, bank, rates)
        ranking.append((client, total_rub))
    ranking.sort(key=lambda pair: pair[1], reverse=True)

    for i, (client, total) in enumerate(ranking[:3], 1):
        print(f'   {i}. {client.full_name}  {total} RUB')

    subsection('Общий баланс банка в RUB')
    total_rub = sum(
        balance_in_rub(acc, rates)
        for acc in bank._accounts.values()
    )
    print(f'   {total_rub:.2f} RUB')

    
    subsection('Аудит')
    print(f'   Всего событий: {len(audit)}')
    print(f'   По уровням:    {audit.count_by_level()}')
    print(f'   По типам:      {audit.count_by_event_type()}')

    subsection('Статистика ошибок')
    errors = audit.get_error_stats()
    if errors:
        for err_type, count in errors.items():
            print(f'   {err_type}: {count}')
    else:
        print('   Ошибок нет')

    subsection('Статистика транзакций')
    print(f"   Выполнено:     {len(results['completed'])}")
    print(f"   Упало:         {len(results['failed'])}")
    print(f"   Заблокировано: {len(results['blocked'])}")
    print(f"   Всего:         {sum(len(v) for v in results.values())}")

def main():
    section('КОМПЛЕКСНАЯ ДЕМОНСТРАЦИЯ БАНКОВСКОЙ СИСТЕМЫ')

    section('1. ИНИЦИАЛИЗАЦИЯ')
    bank, client_ids, accounts = create_bank()
    audit = AuditLog(file_path='audit_day6.log')
    analyzer = RiskAnalyzer(bank, audit)
    processor = TransactionProcessor(bank, analyzer=analyzer, audit=audit)   # ← передать
    print(f'Банк:     {bank.name}')
    print(f'Клиентов: {len(bank._clients)}')
    print(f'Счетов:   {len(bank._accounts)}')

    subsection('Клиенты и счета ')
    for cid in client_ids:
        c = bank._get_client(cid)
        total = client_balance_in_rub(c, bank, processor.rates)
        print(f'   {c.full_name:32s}  счетов: {len(c.account_ids)}  '
            f'баланс: {total:>12.2f} RUB')


    section('2. ТРАНЗАКЦИИ')
    transactions = generate_transactions(bank, accounts)
    print(f'Всего транзакций: {len(transactions)}')

    section('3. ОБРАБОТКА')    
    results = process_transactions(bank, transactions, audit, analyzer, processor)

   
    section('4. СЦЕНАРИЙ КЛИЕНТА')
    show_client_scenario(bank, client_ids[2], audit, processor.rates)
    
    section('5. ОТЧЁТЫ')
    show_reports(bank, audit, results, processor.rates)

async def test_risk_bypass():
    print()
    print("ТЕСТ: прямой execute блокирует риск")

    bank = Bank("TestBank")
    c = Client("Иван", 30, "a@b.ru", "+79991234567", "pass")
    id1 = bank.add_client(c)
    acc1 = bank.open_account(id1, "basic", balance=1_000_000)
    acc2 = bank.open_account(id1, "basic", balance=0)

    audit = AuditLog()
    analyzer = RiskAnalyzer(bank, audit)
    processor = TransactionProcessor(bank, analyzer=analyzer, audit=audit)

    t = Transaction("transfer", 500_000, "RUB",
                    sender_id=acc1.account_id,
                    receiver_id=acc2.account_id)

    processor.execute(t)   
    print(f"\nСтатус: {t.status}")
    print(f"Причина: {t.failure_reason}")

    assert t.status == "failed", f"Должно быть failed, получено {t.status}"
    assert "high risk" in (t.failure_reason or ""), f"Ожидалась блокировка, получено: {t.failure_reason}"
    print(" Транзакция заблокирована напрямую в execute")

    assert acc1._balance == 1_000_000, f"Баланс должен быть нетронут: {acc1._balance}"
    print(f" Баланс acc1 не изменился: {acc1._balance}")

async def test_cumulative_risk():
    print()
    print("ТЕСТ: накопительный риск через прямой execute")

    Bank._allow_operations_24h = True
    bank = Bank("CumulativeBank")
    c = Client("Тестов Тест", 30, "t@t.ru", "+79990000000", "pass")
    cid = bank.add_client(c)
    acc1 = bank.open_account(cid, "basic", balance=10_000_000)
    acc2 = bank.open_account(cid, "basic", balance=0)

    audit = AuditLog()
    analyzer = RiskAnalyzer(bank, audit)
    processor = TransactionProcessor(bank, analyzer=analyzer, audit=audit)

    blocked_at = None
    for i in range(20):
        t = Transaction("transfer", 1000, "RUB",
                        sender_id=acc1.account_id,
                        receiver_id=acc2.account_id)
        processor.execute(t)
        if t.status == "failed" and "high risk" in (t.failure_reason or ""):
            blocked_at = i
            break

    print(f"Заблокировано на операции №{blocked_at}")
    assert blocked_at is not None, "Накопительный риск не сработал — история не ведётся!"
    print(" Накопительный риск сработал")   

async def test_external_fee_by_owner():
    print()
    print("ТЕСТ: комиссия определяется по владельцам, а не по флагу")

    Bank._allow_operations_24h = True
    bank = Bank("FeeTestBank")

    c1 = Client("Клиент Один", 30, "a@a.ru", "+79990000001", "pass1")
    c2 = Client("Клиент Два",  30, "b@b.ru", "+79990000002", "pass2")
    id1 = bank.add_client(c1)
    id2 = bank.add_client(c2)

    a1 = bank.open_account(id1, "basic", balance=100_000)   # клиент 1
    a2 = bank.open_account(id1, "basic", balance=0)         # клиент 1 (тот же)
    a3 = bank.open_account(id2, "basic", balance=0)         # клиент 2 (другой)

    audit = AuditLog()
    analyzer = RiskAnalyzer(bank, audit)
    processor = TransactionProcessor(bank, analyzer=analyzer, audit=audit)

    #  Внутренний: один клиент, без флага is_external
    t_internal = Transaction("transfer", 1000, "RUB",
                             sender_id=a1.account_id,
                             receiver_id=a2.account_id)
    fee_internal = processor._calculate_fee(t_internal)
    print(f"Внутренний (один клиент, is_external=False): fee={fee_internal}")
    assert fee_internal == 0.0, "Внутренний перевод не должен иметь комиссию"

    #  Внешний: разные клиенты, без флага is_external
    t_external = Transaction("transfer", 1000, "RUB",
                             sender_id=a1.account_id,
                             receiver_id=a3.account_id)
    fee_external = processor._calculate_fee(t_external)
    print(f"Внешний (разные клиенты, is_external=False): fee={fee_external}")
    assert fee_external > 0.0, "Внешний перевод должен иметь комиссию"



async def run_all():
    main()
    await test_risk_bypass()
    await test_cumulative_risk()
    await test_external_fee_by_owner()

if __name__ == '__main__':
    import asyncio
    asyncio.run(run_all())

