import { useState } from "react";
import {
  Btn,
  Button,
  Field,
  Panel,
  Heading,
  Tabs,
  Facts,
  Notice,
  Empty,
  Checkbox,
  Textarea,
  DocumentView,
} from "../components/ui";
import { Icon } from "../components/icons";
import { useStore, go } from "../store";
import {
  money,
  contractDocument,
  terms,
  now,
  uid,
  type Doc,
  STATUS,
} from "../domain";
import { FAQList } from "./Public";
import { ARTICLES, MaterialCards } from "./Servicing";
export function Documents() {
  const { state } = useStore();
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("Все");
  const [doc, setDoc] = useState<Doc | null>(null);
  const documents = state.applications
    .flatMap((a) => [
      ...a.docs.map((d) => ({ ...d, application: a.id })),
      ...([
        "approved",
        "alternative",
        "signed",
        "ready",
        "issued",
        "closed",
      ].includes(a.status)
        ? [{ ...contractDocument(a), application: a.id }]
        : []),
    ])
    .filter(
      (d) =>
        (tab === "Все" ||
          (tab === "Договоры" ? d.kind === "Договор" : d.kind !== "Договор")) &&
        d.name.toLowerCase().includes(search.toLowerCase()),
    );
  return (
    <>
      <Heading
        title="Документы"
        description="Файлы по заявкам и демонстрационные договоры"
      />
      <Panel>
        <div className="list-toolbar">
          <Tabs
            items={["Все", "Договоры", "Документы заявок"]}
            value={tab}
            onChange={setTab}
          />
          <Field
            size={48}
            label="Название документа"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {documents.length ? (
          documents.map((d, i) => (
            <div className="document-row" key={d.id + i}>
              <div className="doc-icon">
                <Icon name="document" />
              </div>
              <div>
                <strong>{d.name}</strong>
                <small>
                  Заявка {d.application} ·{" "}
                  {d.status === "accepted"
                    ? "Подтверждено в демо"
                    : "На проверке / на подпись"}
                </small>
              </div>
              <Button view="transparent" size={40} onClick={() => setDoc(d)}>
                Открыть
              </Button>
              <Button
                view="text"
                size={40}
                onClick={() => go("/application/" + d.application)}
              >
                К заявке
              </Button>
            </div>
          ))
        ) : (
          <Empty
            title="Документы не найдены"
            text="Измените поиск или добавьте файл в заявку."
          />
        )}
      </Panel>
      {doc && <DocumentView doc={doc} onClose={() => setDoc(null)} />}
    </>
  );
}
export function Company() {
  const { state, update } = useStore();
  const [tab, setTab] = useState("Данные компании");
  const [updated, setUpdated] = useState(false);
  return (
    <>
      <Heading
        title="Компания и доступ"
        description="ООО «Маяк» · Демонстрационный профиль"
      />
      <Tabs
        items={["Данные компании", "Участники и права", "Источники данных"]}
        value={tab}
        onChange={setTab}
      />
      {tab === "Данные компании" && (
        <Panel>
          <h2>Данные компании</h2>
          <Facts
            items={[
              ["Название", "ООО «Маяк»"],
              ["ИНН", "0000000000 (синтетический)"],
              ["Деятельность", "Оптовая торговля"],
              ["Адрес", "Демо-город, улица Примерная, 1"],
              ["Источник", "Локальный демо-набор"],
            ]}
          />
          <Notice>
            Изменения сведений для конкретной заявки вносятся на шаге
            «Компания». Настоящие реестры не используются.
          </Notice>
          <Btn secondary onClick={() => go("/help?topic=company")}>
            Сообщить об изменении
          </Btn>
        </Panel>
      )}
      {tab === "Участники и права" && (
        <Panel>
          <h2>Кто работает с компанией</h2>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Участник</th>
                  <th>Роль</th>
                  <th>Доступные действия</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Александр Смирнов</td>
                  <td>Руководитель</td>
                  <td>Просмотр, подготовка, отправка, демо-подпись</td>
                </tr>
                <tr>
                  <td>Мария Кузнецова</td>
                  <td>Бухгалтер</td>
                  <td>Просмотр, подготовка и загрузка документов</td>
                </tr>
              </tbody>
            </table>
          </div>
          <Notice>
            Переключение демонстрирует различие интерфейсов. Это не серверная
            защита доступа и не юридическое подтверждение полномочий.
          </Notice>
          <Btn secondary onClick={() => go("/login")}>
            Сменить демонстрационную роль
          </Btn>
        </Panel>
      )}
      {tab === "Источники данных" && (
        <Panel>
          <h2>Источники данных</h2>
          <Facts
            items={[
              ["Профиль компании", "Локальный демо-набор"],
              ["Финансовые сведения", "Введены вручную"],
              ["Документы", "Добавлены участником"],
              [
                "Последнее обновление",
                updated
                  ? new Date().toLocaleString("ru-RU")
                  : "21 октября 2026",
              ],
            ]}
          />
          <Notice>
            Доступ к реальным банковским данным не запрашивается. Обновление
            здесь только имитирует ответ источника.
          </Notice>
          <Btn secondary onClick={() => setUpdated(true)}>
            Обновить демо-данные
          </Btn>
          {updated && (
            <p role="status" className="positive">
              Демо-данные обновлены
            </p>
          )}
        </Panel>
      )}
    </>
  );
}
export function Help({ bank = false }: { bank?: boolean }) {
  const { state, update } = useStore();
  const [subject, setSubject] = useState(
    location.hash.includes("payment")
      ? "Трудности с платежом"
      : "Вопрос по заявке",
  );
  const [text, setText] = useState("");
  const [answer, setAnswer] = useState("");
  const [tab, setTab] = useState(bank ? "Обращения" : "Ответы на вопросы");
  const [selected, setSelected] = useState<string | null>(null);
  const current = state.support.find((c) => c.id === selected);
  return (
    <>
      <Heading
        title={bank ? "Обращения клиентов" : "Помощь"}
        description={
          bank
            ? "Ответьте на вопрос в рамках демонстрационного сценария"
            : "Ответы и обращения — внутри кабинета"
        }
      />
      <Tabs
        items={
          bank
            ? ["Обращения"]
            : ["Ответы на вопросы", "Написать в банк", "Мои обращения"]
        }
        value={tab}
        onChange={setTab}
      />
      {tab === "Ответы на вопросы" && (
        <Panel>
          <FAQList />
          <div className="button-row">
            <Btn secondary onClick={() => setTab("Написать в банк")}>
              Задать вопрос
            </Btn>
          </div>
        </Panel>
      )}
      {tab === "Написать в банк" && (
        <Panel className="narrow-panel">
          <h2>Задайте вопрос</h2>
          <div className="fields">
            <label className="select-label">
              Тема
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              >
                {[
                  "Вопрос по заявке",
                  "Документы и подпись",
                  "Трудности с платежом",
                  "Данные компании",
                  "Доступ в кабинет",
                ].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
            <Textarea
              block
              label="Ваш вопрос"
              minRows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              hint="Опишите ситуацию. Пароли и настоящие данные не нужны."
            />
          </div>
          {subject === "Трудности с платежом" && (
            <Notice tone="orange">
              Обращение само по себе не меняет сроки и суммы. До подтверждения
              новых условий действует текущий график.
            </Notice>
          )}
          <Btn
            disabled={!text.trim()}
            onClick={() => {
              const id =
                "ОБ-" + String(state.support.length + 1).padStart(3, "0");
              if (
                update((s) => ({
                  ...s,
                  support: [
                    {
                      id,
                      subject,
                      text,
                      answer: "",
                      closed: false,
                      date: now(),
                    },
                    ...s.support,
                  ],
                }))
              ) {
                setText("");
                setSelected(id);
                setTab("Мои обращения");
              }
            }}
          >
            Отправить обращение в демо
          </Btn>
        </Panel>
      )}
      {(tab === "Обращения" || tab === "Мои обращения") && (
        <div className="two-col">
          <Panel>
            {state.support.length ? (
              state.support.map((c) => (
                <Button
                  key={c.id}
                  view="transparent"
                  block
                  size={72}
                  className="case-row"
                  onClick={() => {
                    setSelected(c.id);
                    setAnswer(c.answer);
                  }}
                >
                  <div>
                    <strong>{c.subject}</strong>
                    <small>
                      {c.id} ·{" "}
                      {c.closed
                        ? "Завершено"
                        : c.answer
                          ? "Есть ответ"
                          : "Ожидает ответа"}
                    </small>
                  </div>
                  <Icon name="right" />
                </Button>
              ))
            ) : (
              <Empty title="Обращений пока нет" />
            )}
          </Panel>
          <Panel>
            {current ? (
              <>
                <h2>{current.subject}</h2>
                <p className="muted">
                  {current.id} ·{" "}
                  {new Date(current.date).toLocaleDateString("ru-RU")}
                </p>
                <div className="message client">
                  <strong>Клиент</strong>
                  <p>{current.text}</p>
                </div>
                {current.answer && (
                  <div className="message">
                    <strong>Ответ сотрудника</strong>
                    <p>{current.answer}</p>
                  </div>
                )}
                {bank ? (
                  <>
                    <Textarea
                      block
                      label="Ответ клиенту"
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                    />
                    <div className="button-row">
                      <Btn
                        disabled={!answer.trim()}
                        onClick={() =>
                          update((s) => ({
                            ...s,
                            support: s.support.map((c) =>
                              c.id === current.id ? { ...c, answer } : c,
                            ),
                          }))
                        }
                      >
                        Отправить ответ
                      </Btn>
                    </div>
                  </>
                ) : (
                  <>
                    {!current.answer && (
                      <Notice>
                        Обращение принято. Ответ появится здесь после действия
                        сотрудника в демо-кабинете.
                      </Notice>
                    )}
                    {current.answer && !current.closed && (
                      <Btn
                        secondary
                        onClick={() =>
                          update((s) => ({
                            ...s,
                            support: s.support.map((c) =>
                              c.id === current.id ? { ...c, closed: true } : c,
                            ),
                          }))
                        }
                      >
                        Вопрос решён
                      </Btn>
                    )}
                  </>
                )}
              </>
            ) : (
              <Empty title="Выберите обращение" />
            )}
          </Panel>
        </div>
      )}
    </>
  );
}
export function Notifications() {
  const { state, update } = useStore();
  const events = state.applications
    .flatMap((a) =>
      a.history.filter((h) => !h.internal).map((h) => ({ ...h, id: a.id })),
    )
    .sort((a, b) => b.date.localeCompare(a.date));
  const [filter, setFilter] = useState("Все");
  return (
    <>
      <Heading
        title="Уведомления"
        description={
          state.readNotifications
            ? "Все уведомления прочитаны"
            : "События по вашим заявкам и кредитам"
        }
        action={
          <Btn
            secondary
            small
            onClick={() => update((s) => ({ ...s, readNotifications: true }))}
          >
            Отметить всё прочитанным
          </Btn>
        }
      />
      <Tabs
        items={["Все", "Нужно действие"]}
        value={filter}
        onChange={setFilter}
      />
      <Panel>
        {filter === "Нужно действие"
          ? state.applications
              .filter((a) =>
                ["needs_info", "approved", "alternative", "ready"].includes(
                  a.status,
                ),
              )
              .map((a) => (
                <div className="notification-row" key={a.id}>
                  <Icon name="bell" />
                  <div>
                    <strong>{STATUS[a.status].next}</strong>
                    <p>
                      {a.id} · {money(a.amount)}
                    </p>
                  </div>
                  <Btn
                    secondary
                    small
                    onClick={() => go("/application/" + a.id)}
                  >
                    Открыть
                  </Btn>
                </div>
              ))
          : events.map((e, i) => (
              <div className="notification-row" key={i}>
                <Icon name="bell" />
                <div>
                  <strong>{e.text}</strong>
                  <p>
                    {e.id} · {new Date(e.date).toLocaleString("ru-RU")}
                  </p>
                </div>
                <Button
                  view="text"
                  size={40}
                  onClick={() => go("/application/" + e.id)}
                >
                  К заявке
                </Button>
              </div>
            ))}
        {filter === "Нужно действие" &&
          !state.applications.some((a) =>
            ["needs_info", "approved", "alternative", "ready"].includes(
              a.status,
            ),
          ) && <Empty title="Сейчас действий с вашей стороны не требуется" />}
      </Panel>
    </>
  );
}
export function Materials({ id }: { id?: string }) {
  const { state, update } = useStore();
  const a = ARTICLES.find((a) => a.id === id);
  return a ? (
    <>
      <Button view="text" size={40} onClick={() => go("/materials")}>
        К материалам
      </Button>
      <Panel className="article-body">
        <p className="eyebrow">{a.topic} · Материал для прототипа</p>
        <h1>{a.title}</h1>
        <p className="article-lead">{a.text}</p>
        {a.sections.map(([h, t]) => (
          <section key={h}>
            <h2>{h}</h2>
            <p>{t}</p>
          </section>
        ))}
        <Btn onClick={() => go(a.link)}>{a.action}</Btn>
      </Panel>
    </>
  ) : (
    <>
      <Heading
        title="Полезное для бизнеса"
        description="Материалы по вашим задачам"
      />
      <Panel>
        <h2>Настройте темы</h2>
        <div className="topics">
          {["Закупки", "Денежный план", "Документы"].map((t) => (
            <Checkbox
              key={t}
              label={t}
              checked={state.topics.includes(t)}
              onChange={(e) =>
                update((s) => ({
                  ...s,
                  topics: e.target.checked
                    ? [...s.topics, t]
                    : s.topics.filter((x) => x !== t),
                }))
              }
            />
          ))}
        </div>
        <p className="fine-print">
          Подборка меняется по выбранным темам. Авторские материалы прототипа,
          не публикации банка.
        </p>
      </Panel>
      <MaterialCards />
    </>
  );
}
