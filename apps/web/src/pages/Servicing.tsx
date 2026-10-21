import { useState } from "react";
import {
  Btn,
  Button,
  Field,
  Panel,
  Heading,
  Tabs,
  Badge,
  Facts,
  Notice,
  Empty,
  Amount,
  Modal,
  Checkbox,
  download,
} from "../components/ui";
import { Icon } from "../components/icons";
import { useStore, go, event } from "../store";
import {
  money,
  moneyExact,
  terms,
  quote,
  schedule,
  CATALOG,
  STATUS,
  now,
  uid,
  type Application,
} from "../domain";
import { ScheduleModal, ProductCards } from "./Public";
import { History } from "./Applications";
export const ARTICLES = [
  {
    id: "choose",
    topic: "Закупки",
    title: "Кредит или линия: что выбрать для закупок",
    text: "Сначала определите, когда понадобятся деньги: вся сумма сразу или отдельные части в течение срока.",
    sections: [
      [
        "Одна закупка",
        "Если сумму и дату расходов знаете заранее, сравните кредит одной суммой с другими доступными вариантами. Проверьте график возврата и все расходы.",
      ],
      [
        "Закупки в разное время",
        "Кредитная линия позволяет получать деньги траншами в пределах доступного лимита. Для каждого транша проверьте ставку, срок и платежи. По линии могут действовать отдельные комиссии.",
      ],
      [
        "Что сравнить",
        "Сумму на счёт, даты платежей, проценты, комиссии и условия досрочного погашения. Небольшой первый платёж не показывает все расходы.",
      ],
    ],
    action: "Сравнить варианты",
    link: "/products",
  },
  {
    id: "cashflow",
    topic: "Денежный план",
    title: "Если заказчик задерживает оплату",
    text: "Проверьте, какие расходы нужно оплатить до нового срока поступления.",
    sections: [
      [
        "Обновите даты",
        "В денежном плане перенесите ожидаемое поступление. Оставьте расходы и платежи по кредитам на фактических датах.",
      ],
      [
        "Посмотрите разницу",
        "Если по плану денег не хватает, проверьте сумму и период разрыва. При сравнении финансирования учтите платежи по действующим обязательствам.",
      ],
      [
        "Если под угрозой платёж по кредиту",
        "Откройте «Трудности с платежом» и опишите ситуацию. Обращение не меняет график автоматически.",
      ],
    ],
    action: "Открыть денежный план",
    link: "/payments?tab=plan",
  },
  {
    id: "statement",
    topic: "Документы",
    title: "Как подготовить выписку для заявки",
    text: "Сначала откройте требования к документу в своей заявке.",
    sections: [
      [
        "Проверьте период",
        "Выписка должна охватывать период, указанный в запросе банка.",
      ],
      [
        "Проверьте файл",
        "Сверьте формат и размер с требованиями. Убедитесь, что в документе видны реквизиты счёта и операции за нужный период.",
      ],
      [
        "Добавьте документ",
        "Загрузите файл в нужный пункт заявки. Статус «Принят» появится после проверки. В нашем демо используйте только синтетический набор.",
      ],
    ],
    action: "К заявкам",
    link: "/applications",
  },
];
export function MaterialCards() {
  const { state, update } = useStore();
  const visible = ARTICLES.filter((a) => state.topics.includes(a.topic));
  return (
    <>
      <div className="section-heading compact">
        <h2>По вашим задачам</h2>
        <a href="#/materials">Настроить темы</a>
      </div>
      <div className="article-grid">
        {visible.length ? (
          visible.map((a, i) => (
            <article className={"article-card article-" + i} key={a.id}>
              <span className="eyebrow">{a.topic}</span>
              <h3>{a.title}</h3>
              <p>{a.text}</p>
              <a href={"#/materials/" + a.id}>
                Прочитать <Icon name="right" />
              </a>
            </article>
          ))
        ) : (
          <Empty title="Выберите интересные темы">
            <Btn secondary onClick={() => go("/materials")}>
              Настроить темы
            </Btn>
          </Empty>
        )}
      </div>
    </>
  );
}
export function Overview() {
  const { state } = useStore();
  const priority = [
    "needs_info",
    "ready",
    "approved",
    "alternative",
    "signed",
    "draft",
    "review",
  ];
  const next = state.applications
    .filter((a) => priority.includes(a.status))
    .sort((a, b) => priority.indexOf(a.status) - priority.indexOf(b.status))[0];
  const active = state.applications.filter((a) => a.status === "issued");
  const debt = active.reduce((s, a) => s + a.drawn - a.repaid, 0);
  const upcoming = paymentRows(active);
  const first = upcoming[0];
  const sameDay = first ? upcoming.filter((r) => r.date === first.date) : [];
  const pay = first
    ? {
        ...first,
        total: sameDay.reduce((sum, r) => sum + r.total, 0),
        name: sameDay.length > 1 ? "По всем действующим продуктам" : first.name,
      }
    : undefined;
  return (
    <>
      <Heading
        title="Обзор"
        description="ООО «Маяк» · Кредитный кабинет"
        action={<Btn onClick={() => go("/calculator")}>Подобрать кредит</Btn>}
      />
      {next && (
        <Panel className="overview-next">
          <div>
            <span className="badge white">{STATUS[next.status].label}</span>
            <h2>
              {next.status === "draft"
                ? "Продолжим с того же места"
                : next.status === "needs_info"
                  ? "Добавьте сведения по заявке"
                  : next.status === "approved" || next.status === "alternative"
                    ? "Условия готовы"
                    : STATUS[next.status].next}
            </h2>
            <p>
              Заявка {next.id} на {money(next.amount)}.<br />
              {next.status === "draft"
                ? "Начатое сохранено. Продолжите, когда будет удобно."
                : STATUS[next.status].next + "."}
            </p>
            <Button
              size={48}
              view="primary"
              onClick={() =>
                go(
                  next.status === "draft"
                    ? "/apply/" + next.id
                    : "/application/" + next.id,
                )
              }
            >
              {next.status === "draft" ? "Продолжить заявку" : "Открыть заявку"}
            </Button>
          </div>
          <img
            src="/assets/calendar.png"
            alt="Календарь с отметкой выполненной задачи"
          />
        </Panel>
      )}
      <div className="dashboard-grid">
        <Panel className="payment-card">
          <div className="panel-title">
            <h2>Ближайший платёж</h2>
            <Icon name="calendar" />
          </div>
          {pay ? (
            <>
              <span className="muted">
                {new Date(pay.date).toLocaleDateString("ru-RU", {
                  day: "numeric",
                  month: "long",
                })}
              </span>
              <strong className="big-value">{money(pay.total)}</strong>
              <p>{pay.name}</p>
              <Button view="text" size={40} onClick={() => go("/payments")}>
                Посмотреть состав
              </Button>
            </>
          ) : (
            <>
              <div className="big-value">Пока нет</div>
              <p className="muted">
                Платежи появятся после выдачи кредита или транша.
              </p>
              <a href="#/financing">Открыть финансирование</a>
            </>
          )}
        </Panel>
        <Panel>
          <div className="panel-title">
            <h2>Ваше финансирование</h2>
            <Icon name="wallet" />
          </div>
          <Facts
            items={[
              ["Действующие продукты", active.length],
              ["Остаток основного долга", money(debt)],
              [
                "Заявки в работе",
                state.applications.filter(
                  (a) => !["issued", "closed", "rejected"].includes(a.status),
                ).length,
              ],
            ]}
          />
          <a href="#/financing">Все продукты</a>
        </Panel>
        <Panel className="plan-preview">
          <div>
            <h2>Платежи по плану</h2>
            <p>Сопоставьте поступления и расходы с графиком кредита.</p>
            <Btn secondary small onClick={() => go("/payments?tab=plan")}>
              Составить денежный план
            </Btn>
          </div>
          <img src="/assets/calendar.png" alt="Календарь платежей" />
        </Panel>
      </div>
      <MaterialCards />
    </>
  );
}
export function Financing() {
  const { state } = useStore();
  const [tab, setTab] = useState("Действующее");
  const list = state.applications.filter(
    (a) => a.status === "issued" || a.status === "closed",
  );
  return (
    <>
      <Heading
        title="Финансирование"
        description="Ваши кредиты, доступные лимиты и варианты для новых задач"
        action={<Btn onClick={() => go("/calculator")}>Подобрать кредит</Btn>}
      />
      <Tabs
        items={["Действующее", "Новое финансирование"]}
        value={tab}
        onChange={setTab}
      />
      {tab === "Новое финансирование" ? (
        <ProductCards />
      ) : list.length ? (
        <div className="two-col">
          {list.map((a) => (
            <Panel key={a.id}>
              <Badge status={a.status} />
              <h2>{CATALOG[a.product].name}</h2>
              <p className="muted">Демо-договор {a.id}</p>
              <Amount
                value={Math.max(0, a.drawn - a.repaid)}
                label="Остаток основного долга"
              />
              {a.product === "line" && (
                <p>
                  Доступно:{" "}
                  {money(
                    a.status === "closed"
                      ? 0
                      : terms(a).amount - a.drawn + a.repaid,
                  )}
                </p>
              )}
              <Btn secondary onClick={() => go("/credit/" + a.id)}>
                Открыть {a.product === "line" ? "линию" : "кредит"}
              </Btn>
            </Panel>
          ))}
        </div>
      ) : (
        <Panel>
          <Empty
            title="Здесь будут ваши кредиты и линии"
            text="Начните с расчёта — выберите задачу, сумму и срок."
          >
            <Btn onClick={() => setTab("Новое финансирование")}>
              Посмотреть варианты
            </Btn>
          </Empty>
        </Panel>
      )}
    </>
  );
}
export function paymentRows(apps: Application[]) {
  return apps
    .filter((a) => a.status === "issued")
    .flatMap((a) =>
      a.product === "line"
        ? (a.tranches || [])
            .filter((t) => t.amount > t.repaid)
            .flatMap((t) =>
              schedule(t.amount - t.repaid, t.months, t.rate).map((r) => ({
                ...r,
                id: a.id + "-" + t.id + "-" + r.n,
                app: a.id,
                name: "Транш " + t.id,
              })),
            )
        : schedule(a.drawn - a.repaid, terms(a).months, terms(a).rate).map(
            (r) => ({
              ...r,
              id: a.id + "-" + r.n,
              app: a.id,
              name: "Кредит " + a.id,
            }),
          ),
    )
    .sort((a, b) => a.date.localeCompare(b.date));
}
export function Credit({ id }: { id: string }) {
  const { state, change } = useStore();
  const a = state.applications.find((v) => v.id === id);
  const [tab, setTab] = useState("Обзор");
  const [show, setShow] = useState(false);
  const [close, setClose] = useState(false);
  if (!a || !["issued", "closed"].includes(a.status))
    return <Empty title="Действующий продукт не найден" />;
  const t = terms(a);
  const remaining = Math.max(0, a.drawn - a.repaid);
  const payments = paymentRows([a]);
  return (
    <>
      <Heading
        title={(a.product === "line" ? "Кредитная линия № " : "Кредит № ") + id}
        description="Демонстрационный договор · Данные сценария"
        action={<Badge status={a.status} />}
      />
      <Tabs
        items={["Обзор", "График", "Операции", "Условия"]}
        value={tab}
        onChange={setTab}
      />
      {tab === "Обзор" && (
        <>
          <div className="metric-strip">
            <Panel>
              <Amount value={remaining} label="Остаток основного долга" />
            </Panel>
            {a.product === "line" ? (
              <Panel>
                <Amount
                  value={a.status === "closed" ? 0 : t.amount - remaining}
                  label="Доступно для нового транша"
                />
              </Panel>
            ) : (
              <Panel>
                <Amount
                  value={payments[0]?.total ?? 0}
                  label="Следующий платёж"
                />
              </Panel>
            )}
            <Panel>
              <span>Ставка для расчёта</span>
              <strong>{t.rate}%</strong>
              <small>годовых · демо-условия</small>
            </Panel>
          </div>
          <Panel>
            <h2>{a.product === "line" ? "Транши" : "Ближайший платёж"}</h2>
            {a.product === "line" ? (
              <>
                {a.tranches?.length ? (
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Транш</th>
                          <th>Выдано</th>
                          <th>Остаток долга</th>
                          <th>Срок</th>
                        </tr>
                      </thead>
                      <tbody>
                        {a.tranches.map((d) => (
                          <tr key={d.id}>
                            <td>{d.id}</td>
                            <td>{money(d.amount)}</td>
                            <td>{money(d.amount - d.repaid)}</td>
                            <td>{d.months} мес.</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="muted">
                    Траншей пока нет. Открытие линии не означает зачисление
                    денег.
                  </p>
                )}
                {a.status === "issued" && (
                  <Btn
                    disabled={
                      t.amount <= remaining || state.role !== "director"
                    }
                    onClick={() => go("/draw/" + id)}
                  >
                    Новый транш
                  </Btn>
                )}
              </>
            ) : (
              <>
                {payments.length ? (
                  <Facts
                    items={[
                      ["К оплате", money(payments[0].total)],
                      [
                        "Дата платежа",
                        new Date(payments[0].date).toLocaleDateString("ru-RU"),
                      ],
                      ["Счёт погашения", "Демо-счёт • 0001"],
                    ]}
                  />
                ) : (
                  <Notice tone="green">
                    Обязательства в демонстрационном сценарии исполнены.
                  </Notice>
                )}
              </>
            )}
            <div className="button-row">
              <Btn
                secondary
                disabled={remaining <= 0}
                onClick={() => go("/repay/" + id)}
              >
                Досрочное погашение
              </Btn>
              <Button view="text" size={40} onClick={() => setTab("График")}>
                Посмотреть график
              </Button>
              {a.product === "line" && a.status === "issued" && (
                <Button
                  view="text"
                  size={40}
                  disabled={remaining > 0 || state.role !== "director"}
                  onClick={() => setClose(true)}
                >
                  Закрыть линию
                </Button>
              )}
            </div>
            {a.product === "line" &&
              remaining === 0 &&
              a.status === "issued" && (
                <Notice>
                  Задолженности по траншам нет. Линия остаётся открытой;
                  закрытие — отдельное действие.
                </Notice>
              )}
          </Panel>
        </>
      )}
      {tab === "График" && (
        <Panel>
          <h2>Платежи по графику</h2>
          <PaymentTable rows={payments} />
          <p className="fine-print">
            Прогноз демонстрационного сценария. Погашение показано на день
            выдачи; будущие проценты пересчитываются на остаток.
          </p>
        </Panel>
      )}
      {tab === "Операции" && (
        <Panel>
          <History a={a} />
        </Panel>
      )}
      {tab === "Условия" && (
        <Panel>
          <Facts
            items={[
              ["Продукт", CATALOG[a.product].name],
              ["Сумма / лимит", money(t.amount)],
              ["Ставка", t.rate + "% годовых"],
              ["Срок кредита / транша", t.months + " мес."],
              ["Комиссии и услуги", "0 ₽"],
              [
                "Срок линии",
                a.product === "line" ? "24 месяца" : "Не применяется",
              ],
              ["Погашение", "Аннуитет по кредиту или отдельному траншу"],
            ]}
          />
          <Notice>
            Математика демонстрации фиксирована; это не условия реального
            банковского договора.
          </Notice>
        </Panel>
      )}
      {close && (
        <Modal title="Закрыть кредитную линию?" onClose={() => setClose(false)}>
          <p>
            Новые транши по этой демонстрационной линии станут недоступны.
            Документы и история сохранятся.
          </p>
          <Btn
            onClick={() => {
              change(id, (v) => ({
                ...v,
                status: "closed",
                history: [
                  ...v.history,
                  event("Кредитная линия закрыта в демо"),
                ],
              }));
              setClose(false);
            }}
          >
            Закрыть линию в демо
          </Btn>
        </Modal>
      )}
    </>
  );
}
export function Draw({ id }: { id: string }) {
  const { state, change } = useStore();
  const a = state.applications.find((v) => v.id === id);
  const [amount, setAmount] = useState(a?.requestedDraw ?? 500000);
  const [months, setMonths] = useState(a ? terms(a).months : 6);
  const [confirm, setConfirm] = useState(false);
  const [show, setShow] = useState(false);
  if (!a || a.product !== "line" || a.status !== "issued")
    return <Empty title="Транш пока недоступен" />;
  const available = terms(a).amount - a.drawn + a.repaid;
  const q = quote(amount, months, terms(a).rate);
  const currentMonthly = paymentRows(state.applications)
    .filter((r) => r.date === "2026-11-21")
    .reduce((sum, r) => sum + r.total, 0);
  const valid =
    amount >= 10000 &&
    amount <= available &&
    Number.isInteger(months) &&
    months >= 3 &&
    months <= 12;
  return (
    <>
      <Heading
        title="Новый транш"
        description={
          "Кредитная линия № " + id + " · Доступно " + money(available)
        }
      />
      <div className="two-col">
        <Panel>
          <h2>Сколько нужно получить</h2>
          <div className="fields">
            <Field
              label="Сумма транша, ₽"
              type="number"
              value={amount}
              min={10000}
              max={available}
              onChange={(e) => setAmount(Number(e.target.value))}
            />
            <Field
              label="Срок транша, месяцев"
              type="number"
              value={months}
              min={3}
              max={12}
              onChange={(e) => setMonths(Number(e.target.value))}
            />
          </div>
          <Notice>
            Демо-счёт • 0001. Расчёт на день выдачи — 21 октября 2026 года.
          </Notice>
        </Panel>
        <Panel>
          <h2>Условия транша</h2>
          <Facts
            items={[
              ["Поступит в сценарии", money(amount)],
              ["Платёж в месяц", money(q.payment)],
              ["Ставка", terms(a).rate + "% годовых"],
              ["Проценты", money(q.interest)],
              ["Комиссии", "0 ₽"],
              ["Всего выплат", money(q.total)],
              [
                "Платежи 21 ноября с новым траншем",
                money(currentMonthly + q.payment),
              ],
            ]}
          />
          {!valid && (
            <p role="alert" className="field-error">
              Сумма от 10 000 ₽ до доступного лимита. Срок от 3 до 12 месяцев.
            </p>
          )}
          <Btn
            disabled={!valid || state.role !== "director"}
            onClick={() => setConfirm(true)}
          >
            Проверить заявление
          </Btn>
          <Button
            view="text"
            size={40}
            disabled={!valid}
            onClick={() => setShow(true)}
          >
            Посмотреть график
          </Button>
        </Panel>
      </div>
      {show && (
        <ScheduleModal
          amount={amount}
          months={months}
          rate={terms(a).rate}
          onClose={() => setShow(false)}
        />
      )}{" "}
      {confirm && (
        <Modal
          title="Проверьте заявление на транш"
          onClose={() => setConfirm(false)}
        >
          <Facts
            items={[
              ["Сумма", money(amount)],
              ["Срок", months + " мес."],
              ["Счёт", "Демо-счёт • 0001"],
              ["Всего выплат", money(q.total)],
            ]}
          />
          <Notice>
            Подпись и выдача имитируются. Реальные деньги не перечисляются.
          </Notice>
          <Btn
            onClick={() => {
              const ok = change(id, (v) => {
                const limit = terms(v).amount - v.drawn + v.repaid;
                if (amount > limit)
                  throw new Error("Доступный лимит изменился");
                return {
                  ...v,
                  drawn: v.drawn + amount,
                  tranches: [
                    ...(v.tranches || []),
                    {
                      id: String((v.tranches?.length || 0) + 1).padStart(
                        3,
                        "0",
                      ),
                      amount,
                      months,
                      rate: terms(v).rate,
                      repaid: 0,
                      date: now(),
                    },
                  ],
                  history: [
                    ...v.history,
                    event("Транш на " + money(amount) + " выдан в демо"),
                  ],
                };
              });
              if (ok) go("/credit/" + id);
            }}
          >
            Подписать и выдать в демо
          </Btn>
        </Modal>
      )}
    </>
  );
}
export function Repayment({ id }: { id: string }) {
  const { state, change } = useStore();
  const a = state.applications.find((v) => v.id === id);
  const [mode, setMode] = useState("Полностью");
  const [amount, setAmount] = useState(100000);
  const [confirm, setConfirm] = useState(false);
  if (!a || a.status !== "issued")
    return <Empty title="Погашение недоступно" />;
  const remaining = a.drawn - a.repaid;
  const paying = mode === "Полностью" ? remaining : amount;
  const valid = paying > 0 && paying <= remaining;
  const before =
    a.product === "line"
      ? (a.tranches || []).reduce(
          (s, t) => s + quote(t.amount - t.repaid, t.months, t.rate).interest,
          0,
        )
      : quote(remaining, terms(a).months, terms(a).rate).interest;
  const after =
    a.product === "loan"
      ? quote(remaining - paying, terms(a).months, terms(a).rate).interest
      : null;
  return (
    <>
      <Heading title="Досрочное погашение" description={"Демо-договор " + id} />
      <div className="two-col">
        <Panel>
          <h2>Выберите сумму</h2>
          <Tabs
            items={["Полностью", "Частично"]}
            value={mode}
            onChange={setMode}
          />
          {mode === "Частично" && (
            <Field
              label="На погашение основного долга, ₽"
              type="number"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
            />
          )}
          <Facts
            items={[
              ["Основной долг", money(remaining)],
              ["Дата погашения", "21 октября 2026"],
              ["Счёт", "Демо-счёт • 0001"],
            ]}
          />
          <Notice>
            Сценарий погашения в день выдачи: начисленные проценты и комиссии —
            0 ₽. Расчёт на другую дату в этой демонстрации недоступен.
          </Notice>
        </Panel>
        <Panel>
          <h2>Как изменятся обязательства</h2>
          <Facts
            items={[
              ["К списанию в демо", money(paying)],
              [
                "Остаток основного долга",
                money(Math.max(0, remaining - paying)),
              ],
              ["Будущие проценты сейчас", money(before)],
              ...(after !== null
                ? [["Будущие проценты после", money(after)] as [string, string]]
                : []),
            ]}
          />
          <p className="muted">
            {a.product === "line"
              ? "Погашаем транши по порядку выдачи. Возвращённый основной долг восстановит лимит; линия останется открытой."
              : "Срок сохраняется, платёж уменьшается. Полное погашение завершит демонстрационный кредит."}
          </p>
          <Btn
            disabled={!valid || state.role !== "director"}
            onClick={() => setConfirm(true)}
          >
            Проверить погашение
          </Btn>
        </Panel>
      </div>
      {confirm && (
        <Modal
          title="Подтвердить погашение в демо?"
          onClose={() => setConfirm(false)}
        >
          <p>
            В сценарии будет учтено {money(paying)}. Реального списания не
            будет.
          </p>
          <Btn
            onClick={() => {
              const ok = change(id, (v) => {
                let rest = paying;
                if (rest > v.drawn - v.repaid)
                  throw new Error("Сумма изменилась. Обновите расчёт");
                const tranches = v.tranches?.map((t) => {
                  const part = Math.min(rest, t.amount - t.repaid);
                  rest -= part;
                  return { ...t, repaid: t.repaid + part };
                });
                return {
                  ...v,
                  tranches,
                  repaid: v.repaid + paying,
                  status:
                    v.product === "loan" && v.repaid + paying >= v.drawn
                      ? "closed"
                      : v.status,
                  history: [
                    ...v.history,
                    event("Погашение " + money(paying) + " показано в демо"),
                  ],
                };
              });
              if (ok) go("/credit/" + id);
            }}
          >
            Показать погашение в демо
          </Btn>
        </Modal>
      )}
    </>
  );
}
export function PaymentTable({
  rows,
}: {
  rows: ReturnType<typeof paymentRows>;
}) {
  return rows.length ? (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Кредит / транш</th>
            <th>Основной долг</th>
            <th>Проценты</th>
            <th>Всего</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.date).toLocaleDateString("ru-RU")}</td>
              <td>
                <a href={"#/credit/" + r.app}>{r.name}</a>
              </td>
              <td>{moneyExact(r.principal)}</td>
              <td>{moneyExact(r.interest)}</td>
              <td>
                <strong>{moneyExact(r.total)}</strong>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : (
    <Empty
      title="Платежей по графику пока нет"
      text="Они появятся после выдачи кредита или транша."
    />
  );
}
export function Payments() {
  const { state, update } = useStore();
  const [tab, setTab] = useState(
    location.hash.includes("plan") ? "Денежный план" : "По кредитам",
  );
  const [period, setPeriod] = useState("Все");
  const [name, setName] = useState("Оплата заказчика");
  const [amount, setAmount] = useState(500000);
  const [date, setDate] = useState("2026-11-15");
  const [type, setType] = useState<"income" | "expense">("income");
  const opening = state.planOpening ?? 200000;
  const allRows = paymentRows(state.applications);
  const rows = allRows.filter(
    (r) => period === "Все" || r.date.startsWith(period),
  );
  const months = Array.from(new Set(allRows.map((r) => r.date.slice(0, 7))));
  const events = [
    ...state.plan.map((p) => ({
      date: p.date,
      amount: p.type === "income" ? p.amount : -p.amount,
    })),
    ...allRows
      .filter((r) => r.date <= "2026-11-30")
      .map((r) => ({ date: r.date, amount: -r.total })),
  ]
    .filter((e) => e.date <= "2026-11-30")
    .sort((a, b) => a.date.localeCompare(b.date));
  let balance = opening;
  let gap = "";
  for (const e of events) {
    balance += e.amount;
    if (balance < 0 && !gap) gap = e.date;
  }
  return (
    <>
      <Heading
        title="Платёжный календарь"
        description="Платежи по кредитам и денежный план бизнеса"
      />
      <Tabs
        items={["По кредитам", "Денежный план"]}
        value={tab}
        onChange={setTab}
      />
      {tab === "По кредитам" ? (
        <Panel>
          <div className="list-toolbar">
            <label className="select-label">
              Период
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
              >
                <option>Все</option>
                {months.map((m) => (
                  <option key={m}>{m}</option>
                ))}
              </select>
            </label>
            <div>
              <span className="muted">По графику за период</span>
              <h2>{money(rows.reduce((s, r) => s + r.total, 0))}</h2>
            </div>
            <Btn
              secondary
              small
              onClick={() =>
                download(
                  "demo-payments.csv",
                  "Дата;Кредит;Платёж\n" +
                    rows
                      .map((r) => [r.date, r.name, r.total].join(";"))
                      .join("\n"),
                  "text/csv;charset=utf-8",
                )
              }
            >
              Скачать график
            </Btn>
          </div>
          <PaymentTable rows={rows} />
        </Panel>
      ) : (
        <>
          <Panel>
            <h2>Проверьте, хватит ли денег</h2>
            <p className="muted">
              Период плана: 21 октября — 30 ноября 2026. Платежи по кредитам
              учтены автоматически.
            </p>
            <Field
              label="Остаток на начало периода, ₽"
              type="number"
              min={0}
              value={opening}
              onChange={(e) =>
                update((s) => ({ ...s, planOpening: Number(e.target.value) }))
              }
            />
            <div className="fields plan-fields">
              <Field
                label="Название"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              <label className="select-label">
                Тип
                <select
                  value={type}
                  onChange={(e) =>
                    setType(e.target.value as "income" | "expense")
                  }
                >
                  <option value="income">Поступление</option>
                  <option value="expense">Расход</option>
                </select>
              </label>
              <Field
                label="Сумма, ₽"
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
              />
              <Field
                label="Дата"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
            <Btn
              secondary
              disabled={
                !name.trim() ||
                !Number.isFinite(amount) ||
                amount <= 0 ||
                date < "2026-10-21" ||
                date > "2026-11-30"
              }
              onClick={() =>
                update((s) => ({
                  ...s,
                  plan: [...s.plan, { id: uid(), name, amount, date, type }],
                }))
              }
            >
              Добавить в план
            </Btn>
            {state.plan.map((p) => (
              <div className="plan-row" key={p.id}>
                <div>
                  <strong>{p.name}</strong>
                  <small>{p.date}</small>
                </div>
                <strong className={p.type === "income" ? "positive" : ""}>
                  {p.type === "income" ? "+" : "−"} {money(p.amount)}
                </strong>
                <Button
                  view="transparent"
                  size={40}
                  onClick={() =>
                    update((s) => ({
                      ...s,
                      plan: s.plan.filter((x) => x.id !== p.id),
                    }))
                  }
                  aria-label={"Удалить запись " + p.name}
                >
                  ×
                </Button>
              </div>
            ))}
          </Panel>
          <Panel>
            <h2>
              {gap
                ? "По плану есть недостаток средств"
                : "По этому плану денег хватает на платежи"}
            </h2>
            {gap && (
              <p>
                Первый разрыв — {new Date(gap).toLocaleDateString("ru-RU")}.
                Проверьте даты поступлений и расходов.
              </p>
            )}
            <Amount label="Остаток на конец периода" value={balance} />
            <Notice>
              Прогноз по демонстрационному сценарию. Не добавляйте кредитные
              платежи повторно в расходы.
            </Notice>
            <Button
              view="text"
              size={40}
              onClick={() => go("/help?topic=payment")}
            >
              Сообщить о трудностях с платежом
            </Button>
          </Panel>
        </>
      )}
    </>
  );
}
