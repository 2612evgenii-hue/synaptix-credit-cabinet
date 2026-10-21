import { useState, type ChangeEvent } from "react";
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
  Checkbox,
  Textarea,
  Modal,
  DocumentView,
} from "../components/ui";
import { Icon } from "../components/icons";
import { useStore, go, event } from "../store";
import {
  CATALOG,
  STATUS,
  money,
  contractDocument,
  terms,
  quote,
  dateLabel,
  now,
  uid,
  demoDocument,
  transition,
  validateApplication,
  type Application,
  type Doc,
  type Status,
} from "../domain";
import { ScheduleModal } from "./Public";
export function Applications({ bank = false }: { bank?: boolean }) {
  const { state } = useStore();
  const [filter, setFilter] = useState("Все");
  const [search, setSearch] = useState("");
  const list = state.applications
    .filter((a) => !bank || a.status !== "draft")
    .filter(
      (a) =>
        !search ||
        [a.id, a.company, a.inn].some((t) =>
          t.toLowerCase().includes(search.toLowerCase()),
        ),
    )
    .filter(
      (a) =>
        filter === "Все" ||
        (filter === "Нужно действие"
          ? (bank
              ? ["review", "signed"]
              : ["draft", "needs_info", "approved", "alternative", "ready"]
            ).includes(a.status)
          : filter === "На рассмотрении"
            ? ["review", "signed"].includes(a.status)
            : ["issued", "closed", "rejected"].includes(a.status)),
    );
  return (
    <>
      <Heading
        title={bank ? "Заявки на финансирование" : "Заявки"}
        description={
          bank
            ? "Проверьте сведения и определите следующий шаг"
            : "Продолжайте оформление и следите за решениями"
        }
        action={
          !bank && <Btn onClick={() => go("/calculator")}>Новая заявка</Btn>
        }
      />
      {bank && (
        <div className="metric-strip">
          {[
            [
              "В очереди",
              state.applications.filter((a) => a.status === "review").length,
            ],
            [
              "Ожидаем сведения",
              state.applications.filter((a) => a.status === "needs_info")
                .length,
            ],
            [
              "Готовность к выдаче",
              state.applications.filter((a) => a.status === "signed").length,
            ],
          ].map(([k, v]) => (
            <Panel key={k}>
              <span>{k}</span>
              <strong>{v}</strong>
            </Panel>
          ))}
        </div>
      )}
      <Panel>
        <div className="list-toolbar">
          <Tabs
            items={["Все", "Нужно действие", "На рассмотрении", "Завершённые"]}
            value={filter}
            onChange={setFilter}
          />
          <Field
            size={48}
            label={bank ? "Заявка, компания или ИНН" : "Номер заявки"}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {list.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>{bank ? "Компания / заявка" : "Заявка / продукт"}</th>
                  <th>Сумма / лимит</th>
                  <th>Статус</th>
                  <th>{bank ? "Ответственный" : "Следующий шаг"}</th>
                  <th>
                    <span className="sr-only">Действие</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {list.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <a
                        className="table-link"
                        href={
                          "#/" +
                          (bank
                            ? "bank/application/"
                            : a.status === "draft"
                              ? "apply/"
                              : "application/") +
                          a.id
                        }
                      >
                        {bank ? a.company : a.id}
                      </a>
                      <small>{bank ? a.id : CATALOG[a.product].name}</small>
                    </td>
                    <td className="nowrap">
                      {money(a.amount)}
                      <small>{a.months} мес.</small>
                    </td>
                    <td>
                      <Badge status={a.status} />
                    </td>
                    <td className="next-cell">
                      {bank ? a.owner || "Не назначен" : STATUS[a.status].next}
                    </td>
                    <td>
                      <Button
                        view="transparent"
                        size={40}
                        aria-label={"Открыть заявку " + a.id}
                        onClick={() =>
                          go(
                            "/" +
                              (bank
                                ? "bank/application/"
                                : a.status === "draft"
                                  ? "apply/"
                                  : "application/") +
                              a.id,
                          )
                        }
                      >
                        <Icon name="right" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            title="Заявки не найдены"
            text="Измените запрос или сбросьте фильтры"
          >
            <Btn
              secondary
              onClick={() => {
                setSearch("");
                setFilter("Все");
              }}
            >
              Сбросить фильтры
            </Btn>
          </Empty>
        )}
      </Panel>
    </>
  );
}
export function DocumentList({
  a,
  editable = false,
}: {
  a: Application;
  editable?: boolean;
}) {
  const { change } = useStore();
  const [doc, setDoc] = useState<Doc | null>(null);
  const [error, setError] = useState("");
  const add = (d: Doc) =>
    change(a.id, (v) => ({
      ...v,
      docs: [...v.docs, d],
      history: [...v.history, event("Добавлен документ: " + d.name)],
    }));
  const upload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    if (!/\.(txt|pdf)$/i.test(file.name)) {
      setError("Допустимы TXT и PDF из демо-набора");
      return;
    }
    if (file.size > 1024 * 1024) {
      setError("Файл больше 1 МБ");
      return;
    }
    const data = file.name.toLowerCase().endsWith(".pdf")
      ? await new Promise<string>((resolve, reject) => {
          const r = new FileReader();
          r.onload = () => resolve(String(r.result));
          r.onerror = () => reject(new Error("Не удалось прочитать файл"));
          r.readAsDataURL(file);
        })
      : await file.text();
    add({
      id: uid(),
      name: file.name,
      kind: "Документ к заявке",
      mime: file.name.toLowerCase().endsWith(".pdf")
        ? "application/pdf"
        : "text/plain",
      data,
      status: "added",
      date: now(),
    });
    e.target.value = "";
  };
  return (
    <>
      {editable && (
        <div className="upload-area">
          <Icon name="document" />
          <h3>Добавьте документы</h3>
          <p>Выписка за 6 месяцев · TXT или PDF · до 1 МБ</p>
          <p className="fine-print">
            Только синтетические файлы. Не загружайте настоящие документы.
          </p>
          <div className="button-row">
            <Btn secondary small onClick={() => add(demoDocument())}>
              Добавить демо-выписку
            </Btn>
            <label className="file-input-label">
              Выбрать файл
              <input
                aria-label="Добавить файл из демо-набора"
                type="file"
                accept=".txt,.pdf"
                onChange={(e) => {
                  void upload(e).catch(() =>
                    setError("Не удалось прочитать файл. Попробуйте ещё раз."),
                  );
                }}
              />
            </label>
          </div>
        </div>
      )}
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      {a.docs.length
        ? a.docs.map((d) => (
            <div className="document-row" key={d.id}>
              <div className="doc-icon">
                <Icon name="document" />
              </div>
              <div>
                <strong>{d.name}</strong>
                <small>
                  {dateLabel(d.date)} ·{" "}
                  {d.status === "accepted"
                    ? "Принят в демо"
                    : "Загружен, проверка не завершена"}
                </small>
              </div>
              <Button view="transparent" size={40} onClick={() => setDoc(d)}>
                Открыть
              </Button>
            </div>
          ))
        : !editable && <p className="muted">Документы ещё не добавлены</p>}
      {doc && <DocumentView doc={doc} onClose={() => setDoc(null)} />}
    </>
  );
}
export function ApplicationForm({ id }: { id: string }) {
  const { state, change, error } = useStore();
  const a = state.applications.find((v) => v.id === id);
  const [agreed, setAgreed] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [submitted, setSubmitted] = useState(false);
  if (!a) return <Empty title="Заявка не найдена" />;
  if (a.status !== "draft") return <ApplicationDetail id={id} />;
  const steps = ["Компания", "Финансы", "Документы", "Участники", "Проверка"];
  const set = (p: Partial<Application>) => change(id, (v) => ({ ...v, ...p }));
  const step = a.step;
  const submit = () => {
    const es = validateApplication(a);
    if (!agreed) es.push("Подтвердите верность демонстрационных сведений");
    setErrors(es);
    if (es.length) return;
    const ok = change(id, (v) =>
      transition(
        v,
        "review",
        state.role!,
        "Демо-заявка принята на рассмотрение",
      ),
    );
    if (ok) setSubmitted(true);
  };
  return (
    <>
      <Heading
        title="Заявка на финансирование"
        description={CATALOG[a.product].name + " · " + money(a.amount)}
        action={
          <span className="saved-label">
            <Icon name="check" />
            {error
              ? "Есть несохранённые изменения"
              : "Сохранено в этом браузере"}
          </span>
        }
      />
      <div className="form-layout">
        <aside className="form-steps">
          {steps.map((s, i) => (
            <Button
              key={s}
              view="transparent"
              size={48}
              className={i === step ? "form-step active" : "form-step"}
              onClick={() => set({ step: i })}
            >
              <span className="step-circle">
                {i < step ? <Icon name="check" /> : i + 1}
              </span>
              {s}
            </Button>
          ))}
          <div className="step-hint">
            {error ? (
              "Сохранение недоступно. Освободите место в браузере и повторите изменение."
            ) : (
              <>
                Можно прерваться.
                <br />
                Изменения сохраняются в этом браузере.
              </>
            )}
          </div>
        </aside>
        <Panel className="form-panel">
          {step === 0 && (
            <>
              <p className="eyebrow">Шаг 1 из 5</p>
              <h2>Проверьте данные компании</h2>
              <p className="muted">
                Демо-сведения уже заполнены. Проверьте их и добавьте
                недостающее.
              </p>
              <div className="fields">
                <Field
                  label="Название компании"
                  value={a.company}
                  onChange={(e) => set({ company: e.target.value })}
                />
                <div className="two-col">
                  <Field
                    label="ИНН"
                    value={a.inn}
                    maxLength={12}
                    onChange={(e) => set({ inn: e.target.value })}
                    hint="Синтетический ИНН для демонстрации"
                  />
                  <Field
                    label="Вид деятельности"
                    value={a.activity}
                    onChange={(e) => set({ activity: e.target.value })}
                  />
                </div>
                <Field
                  label="Адрес ведения бизнеса"
                  value={a.address}
                  onChange={(e) => set({ address: e.target.value })}
                />
              </div>
              <Notice>
                Источник: демонстрационный профиль компании. Реальные реестры не
                запрашиваются.
              </Notice>
            </>
          )}
          {step === 1 && (
            <>
              <p className="eyebrow">Шаг 2 из 5</p>
              <h2>Расскажите о финансах бизнеса</h2>
              <p className="muted">
                Укажите показатели за апрель — сентябрь 2026. Ноль и
                незаполненное поле — разные значения.
              </p>
              <div className="fields two-col">
                {(
                  [
                    ["revenue", "Выручка за 6 месяцев"],
                    ["expenses", "Расходы за 6 месяцев"],
                    ["debt", "Остаток по кредитам и займам"],
                    ["payment", "Платежи по кредитам за месяц"],
                  ] as const
                ).map(([key, label]) => (
                  <Field
                    key={key}
                    label={label}
                    type="number"
                    min={0}
                    value={a[key]}
                    onChange={(e) => set({ [key]: e.target.value })}
                    rightAddons={<span>₽</span>}
                  />
                ))}
              </div>
              <Button
                view="text"
                size={40}
                onClick={() =>
                  set({
                    revenue: "12000000",
                    expenses: "8000000",
                    debt: "0",
                    payment: "0",
                  })
                }
              >
                Заполнить примером из демо-набора
              </Button>
              <Textarea
                block
                label="Комментарий"
                value={a.comment}
                onChange={(e) => set({ comment: e.target.value })}
              />
            </>
          )}
          {step === 2 && (
            <>
              <p className="eyebrow">Шаг 3 из 5</p>
              <h2>Документы к заявке</h2>
              <p className="muted">
                Выписка помогает сопоставить обороты с финансовыми сведениями.
              </p>
              <DocumentList a={a} editable />
            </>
          )}
          {step === 3 && (
            <>
              <p className="eyebrow">Шаг 4 из 5</p>
              <h2>Кто участвует в оформлении</h2>
              <p className="muted">
                Подготовку заявки и подписание можно поручить разным участникам.
              </p>
              <div className="person-row">
                <span className="avatar">АС</span>
                <div>
                  <strong>Александр Смирнов</strong>
                  <p>Руководитель · подготовка, отправка и подпись в демо</p>
                </div>
                <span className="badge green">Подписант</span>
              </div>
              <div className="person-row">
                <span className="avatar beige">МК</span>
                <div>
                  <strong>Мария Кузнецова</strong>
                  <p>Бухгалтер · подготовка и документы</p>
                </div>
              </div>
              <Notice>
                Демонстрационные участники. Полномочия моделируются локально;
                юридически значимой подписи нет.
              </Notice>
            </>
          )}
          {step === 4 && (
            <>
              <p className="eyebrow">Шаг 5 из 5</p>
              <h2>Проверьте заявку</h2>
              <Facts
                items={[
                  ["Компания", a.company],
                  ["Цель", a.goal],
                  [a.product === "line" ? "Лимит" : "Сумма", money(a.amount)],
                  [
                    a.product === "line"
                      ? "Срок первого транша"
                      : "Срок кредита",
                    a.months + " мес.",
                  ],
                  [
                    "Выручка за 6 месяцев",
                    a.revenue !== "" ? money(Number(a.revenue)) : "Не указана",
                  ],
                  ["Документы", a.docs.length + " файл(ов)"],
                  ["Подписант", "Александр Смирнов"],
                ]}
              />
              <Checkbox
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                label="Подтверждаю верность демонстрационных сведений"
              />
              <p className="fine-print">
                Заявка появится в демо-очереди сотрудника. Кредитный договор на
                этом шаге не заключается.
              </p>
              {state.role === "accountant" && (
                <Notice tone="orange">
                  Отправка доступна руководителю. Сведения сохранены — смените
                  демонстрационную роль на экране входа.
                </Notice>
              )}
            </>
          )}
          {errors.length > 0 && (
            <div role="alert" className="error-summary">
              <strong>Проверьте сведения</strong>
              <ul>
                {errors.map((e) => (
                  <li key={e}>{e}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="form-actions">
            <Button
              view="secondary"
              size={48}
              onClick={() =>
                step ? set({ step: step - 1 }) : go("/applications")
              }
            >
              {step ? "Назад" : "К заявкам"}
            </Button>
            {step < 4 ? (
              <Btn onClick={() => set({ step: step + 1 })}>Продолжить</Btn>
            ) : (
              <Btn disabled={state.role !== "director"} onClick={submit}>
                Отправить демо-заявку
              </Btn>
            )}
          </div>
          <Button
            view="text"
            size={40}
            disabled={!!error}
            onClick={() => go("/applications")}
          >
            Сохранить и выйти
          </Button>
        </Panel>
      </div>
      {submitted && (
        <Modal
          title="Демо-заявка принята"
          onClose={() => go("/application/" + id)}
        >
          <div className="success-mark">
            <Icon name="check" />
          </div>
          <p>Номер {id}. Статус и запросы банка появятся на странице заявки.</p>
          <Btn onClick={() => go("/application/" + id)}>Открыть заявку</Btn>
        </Modal>
      )}
    </>
  );
}
export function History({
  a,
  internal = false,
}: {
  a: Application;
  internal?: boolean;
}) {
  return (
    <div className="timeline">
      {a.history
        .filter((e) => internal || !e.internal)
        .slice()
        .reverse()
        .map((e, i) => (
          <div key={i}>
            <span className="timeline-dot" />
            <strong>{e.text}</strong>
            <p>
              {new Date(e.date).toLocaleString("ru-RU")} · {e.actor}
            </p>
          </div>
        ))}
    </div>
  );
}
export function ApplicationDetail({ id }: { id: string }) {
  const { state, change } = useStore();
  const a = state.applications.find((v) => v.id === id);
  const [tab, setTab] = useState("Обзор заявки");
  const [comment, setComment] = useState("");
  if (!a) return <Empty title="Заявка не найдена" />;
  return (
    <>
      <Heading
        title={"Заявка № " + id}
        description={CATALOG[a.product].name + " · " + money(a.amount)}
        action={<Badge status={a.status} />}
      />
      <Tabs
        items={["Обзор заявки", "Данные и документы", "Участники", "История"]}
        value={tab}
        onChange={setTab}
      />
      {tab === "Обзор заявки" && (
        <>
          <Panel className="next-action">
            <div className="action-mark">
              <Icon name={a.status === "needs_info" ? "document" : "check"} />
            </div>
            <div>
              <p className="eyebrow">Следующий шаг</p>
              <h2>{STATUS[a.status].label}</h2>
              <p>{STATUS[a.status].next}</p>
              {a.status === "review" && (
                <p className="muted">
                  Если понадобятся сведения, запрос появится здесь. Для
                  продолжения демонстрации откройте кабинет сотрудника.
                </p>
              )}
              {a.status === "rejected" && (
                <p>
                  {a.clientReason ||
                    "Решение принято по результатам рассмотрения этой демонстрационной заявки."}
                </p>
              )}
              {["approved", "alternative"].includes(a.status) && (
                <Btn onClick={() => go("/offer/" + id)}>Посмотреть условия</Btn>
              )}
              {a.status === "draft" && (
                <Btn onClick={() => go("/apply/" + id)}>Продолжить заявку</Btn>
              )}
              {a.status === "ready" && (
                <Btn onClick={() => go("/sign/" + id)}>Оформить выдачу</Btn>
              )}
              {a.status === "issued" && (
                <Btn onClick={() => go("/credit/" + id)}>
                  Открыть {a.product === "line" ? "линию" : "кредит"}
                </Btn>
              )}
            </div>
          </Panel>
          {a.status === "needs_info" && (
            <Panel>
              <h2>Добавьте сведения по заявке</h2>
              <Notice tone="orange">{a.request}</Notice>
              <DocumentList a={a} editable />
              <Textarea
                block
                label="Комментарий к документам"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
              />
              <div className="button-row">
                <Btn
                  disabled={
                    state.role !== "director" ||
                    (!comment.trim() &&
                      a.docs.length <= (a.requestDocCount ?? a.docs.length))
                  }
                  onClick={() =>
                    change(id, (v) => ({
                      ...transition(
                        v,
                        "review",
                        state.role!,
                        "Ответ на запрос получен" +
                          (comment ? ": " + comment : ""),
                      ),
                      request: "",
                    }))
                  }
                >
                  Отправить сведения
                </Btn>
              </div>
            </Panel>
          )}
          <div className="two-col">
            <Panel>
              <h2>Параметры заявки</h2>
              <Facts
                items={[
                  ["Задача", a.goal],
                  ["Запрошено", money(a.amount)],
                  [
                    a.product === "line"
                      ? "Срок первого транша"
                      : "Срок кредита",
                    a.months + " мес.",
                  ],
                  ["Компания", a.company],
                  ["Ответственный", a.owner || "Пока не назначен"],
                ]}
              />
            </Panel>
            <Panel>
              <h2>Последние события</h2>
              <History a={{ ...a, history: a.history.slice(-3) }} />
            </Panel>
          </div>
        </>
      )}
      {tab === "Данные и документы" && (
        <Panel>
          <h2>Сведения о бизнесе</h2>
          <Facts
            items={[
              ["Компания", a.company],
              ["ИНН", a.inn],
              [
                "Выручка за 6 месяцев",
                a.revenue ? money(Number(a.revenue)) : "Не указана",
              ],
              [
                "Расходы за 6 месяцев",
                a.expenses ? money(Number(a.expenses)) : "Не указаны",
              ],
            ]}
          />
          <h2>Документы</h2>
          <DocumentList a={a} />
        </Panel>
      )}
      {tab === "Участники" && (
        <Panel>
          <h2>Участники заявки</h2>
          <Facts
            items={[
              ["Руководитель", "Александр Смирнов — отправка и подпись"],
              ["Бухгалтер", "Мария Кузнецова — подготовка"],
              ["Банк", a.owner || "Не назначен"],
            ]}
          />
        </Panel>
      )}
      {tab === "История" && (
        <Panel>
          <History a={a} />
        </Panel>
      )}
      <Button
        view="text"
        size={40}
        onClick={() => go("/help?application=" + id)}
      >
        Задать вопрос по заявке
      </Button>
    </>
  );
}
export function Offer({ id }: { id: string }) {
  const { state } = useStore();
  const a = state.applications.find((v) => v.id === id);
  const [show, setShow] = useState(false);
  if (
    !a ||
    !["approved", "alternative", "signed", "ready", "issued"].includes(a.status)
  )
    return <Empty title="Предложение пока недоступно" />;
  const t = terms(a);
  const q = quote(
    a.product === "line"
      ? Math.min(a.requestedDraw ?? 500000, t.amount)
      : t.amount,
    t.months,
    t.rate,
  );
  return (
    <>
      <Heading
        title="Ваши условия"
        description={CATALOG[a.product].name + " · Заявка № " + id}
        action={<span className="badge gray">Версия {a.version}</span>}
      />
      <div className="offer-grid">
        <Panel>
          <p className="eyebrow">Предложение в демо</p>
          <h2>
            {a.product === "line" ? "Лимит по договору" : "Сумма кредита"}
          </h2>
          <div className="offer-amount">{money(t.amount)}</div>
          <Facts
            items={[
              [
                a.product === "line" ? "Срок первого транша" : "Срок кредита",
                t.months + " мес.",
              ],
              ...(a.product === "line"
                ? [["Срок линии", "24 месяца"] as [string, string]]
                : []),
              ["Ставка", t.rate + "% годовых"],
              ["Обеспечение", "Не требуется в демо"],
              ["Комиссии и услуги", "0 ₽"],
            ]}
          />
          {a.status === "alternative" && (
            <Notice tone="orange">
              <strong>Условия отличаются от заявки</strong>
              <p>
                В заявке: {money(a.amount)} на {a.months} мес., предварительная
                ставка {a.rate}% годовых. В предложении: {money(t.amount)} на{" "}
                {t.months} мес., ставка {t.rate}% годовых.
              </p>
            </Notice>
          )}
        </Panel>
        <Panel className="offer-cost">
          <h2>Сколько нужно вернуть</h2>
          {a.product === "line" && (
            <Notice>
              Пример для первого транша на{" "}
              {money(Math.min(a.requestedDraw ?? 500000, t.amount))}. Будущие
              транши не включены. Расходы по самой линии в демо — 0 ₽.
            </Notice>
          )}
          <Facts
            items={[
              ["Платёж в месяц", money(q.payment)],
              ["Проценты за срок", money(q.interest)],
              ["Всего выплат по графику", money(q.total)],
              ["Расходы вне графика", "0 ₽"],
            ]}
          />
          <Button view="text" size={40} onClick={() => setShow(true)}>
            Посмотреть график
          </Button>
          <div className="divider" />
          <h3>Что нужно для получения денег</h3>
          <p>
            Проверьте и подпишите демо-документы. Сотрудник подтвердит
            готовность к выдаче.
          </p>
          <Btn block onClick={() => go("/sign/" + id)}>
            Перейти к документам
          </Btn>
        </Panel>
      </div>
      <Notice>
        Условия вымышлены. Это не предложение Альфа-Банка и не кредитный
        договор.
      </Notice>
      {show && (
        <ScheduleModal
          amount={
            a.product === "line"
              ? Math.min(a.requestedDraw ?? 500000, t.amount)
              : t.amount
          }
          months={t.months}
          rate={t.rate}
          onClose={() => setShow(false)}
        />
      )}
    </>
  );
}
export function Signing({ id }: { id: string }) {
  const { state, change } = useStore();
  const a = state.applications.find((v) => v.id === id);
  const [checked, setChecked] = useState(false);
  const [doc, setDoc] = useState<Doc | null>(null);
  const [confirm, setConfirm] = useState(false);
  if (
    !a ||
    !["approved", "alternative", "signed", "ready", "issued"].includes(a.status)
  )
    return <Empty title="Документы для подписи пока недоступны" />;
  const t = terms(a);
  const contract = contractDocument(a);
  return (
    <>
      <Heading
        title={
          a.status === "ready"
            ? "Можно оформить выдачу"
            : "Проверьте документы перед подписанием"
        }
        description={"Заявка № " + id + " · Версия условий " + a.version}
      />
      <Panel>
        <Facts
          items={[
            ["Продукт", CATALOG[a.product].name],
            ["Сумма / лимит", money(t.amount)],
            ["Ставка", t.rate + "% годовых"],
            [
              a.product === "line" ? "Срок первого транша" : "Срок кредита",
              t.months + " мес.",
            ],
            ...(a.product === "line"
              ? [["Срок линии", "24 месяца"] as [string, string]]
              : []),
            ["Подписант", "Александр Смирнов, руководитель"],
          ]}
        />
        <div className="document-row">
          <Icon name="document" />
          <div>
            <strong>Демо-договор и условия</strong>
            <small>Версия {a.version} · TXT</small>
          </div>
          <Btn small secondary onClick={() => setDoc(contract)}>
            Открыть
          </Btn>
        </div>
        {["approved", "alternative"].includes(a.status) ? (
          <>
            <Checkbox
              label="Проверил сумму, ставку, расходы и условия"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
            />
            <p className="fine-print">
              Имитируем подписание. Юридически значимая подпись не создаётся.
            </p>
            <Btn
              disabled={!checked || state.role !== "director"}
              onClick={() =>
                change(id, (v) => ({
                  ...transition(
                    v,
                    "signed",
                    state.role!,
                    "Подписание выполнено в демо, версия " + v.version,
                  ),
                  signedVersion: v.version,
                }))
              }
            >
              Подписать и отправить в демо
            </Btn>
            {state.role !== "director" && (
              <Notice>
                Подписание доступно руководителю. Смените демонстрационную роль
                на экране входа.
              </Notice>
            )}
          </>
        ) : a.status === "signed" ? (
          <Notice tone="blue">
            <strong>Подписание выполнено в демо</strong>
            <p>
              Сотрудник банка проверит документы и подтвердит готовность. Выдача
              ещё не выполнена.
            </p>
          </Notice>
        ) : a.status === "ready" ? (
          <>
            <Notice tone="green">
              Подписание и готовность подтверждены для версии {a.version}.
            </Notice>
            <Facts
              items={[
                ["Счёт зачисления", "Демо-счёт • 0001"],
                [
                  a.product === "line" ? "Лимит линии" : "Поступит в сценарии",
                  money(t.amount),
                ],
                ["Удержания", "0 ₽"],
              ]}
            />
            <Btn
              disabled={state.role !== "director"}
              onClick={() => setConfirm(true)}
            >
              {a.product === "line"
                ? "Открыть линию в демо"
                : "Запросить выдачу в демо"}
            </Btn>
          </>
        ) : (
          <Notice tone="green">
            {a.product === "line"
              ? "Линия открыта в демо. Транши оформляются отдельно."
              : "Выдача показана в демо. Реальные деньги не перечислялись."}
            <p>
              <a href={"#/credit/" + id}>
                Открыть {a.product === "line" ? "линию" : "кредит"}
              </a>
            </p>
          </Notice>
        )}
      </Panel>
      {doc && <DocumentView doc={doc} onClose={() => setDoc(null)} />}{" "}
      {confirm && (
        <Modal title="Проверьте действие" onClose={() => setConfirm(false)}>
          <p>
            {a.product === "line"
              ? "Откроем демонстрационную линию. Зачисления денег пока нет."
              : "В сценарии на демо-счёт • 0001 поступит " +
                money(t.amount) +
                ". Реальные деньги не перечисляются."}
          </p>
          <Btn
            onClick={() => {
              if (
                change(id, (v) => ({
                  ...transition(
                    v,
                    "issued",
                    state.role!,
                    v.product === "line"
                      ? "Линия открыта в демо"
                      : "Выдача показана в демо",
                  ),
                  drawn: v.product === "line" ? 0 : t.amount,
                }))
              )
                go("/credit/" + id);
            }}
          >
            Подтвердить в демо
          </Btn>
        </Modal>
      )}
    </>
  );
}
