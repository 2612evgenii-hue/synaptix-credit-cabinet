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
  Checkbox,
  Textarea,
  Modal,
} from "../components/ui";
import { useStore, go, event } from "../store";
import { CATALOG, money, quote, transition, type Status } from "../domain";
import { DocumentList, History } from "./Applications";
export function BankDossier({ id }: { id: string }) {
  const { state, change } = useStore();
  const a = state.applications.find((v) => v.id === id);
  const [tab, setTab] = useState("Досье");
  const [request, setRequest] = useState(
    "Добавьте выписку за апрель — сентябрь 2026 года с оборотами по счёту.",
  );
  const [amount, setAmount] = useState(a?.amount ?? 0);
  const [months, setMonths] = useState(a?.months ?? 12);
  const [rate, setRate] = useState(a?.rate ?? 16);
  const [comment, setComment] = useState(a?.internalComment ?? "");
  const [checks, setChecks] = useState(false);
  const [checkError, setCheckError] = useState(false);
  const [confirm, setConfirm] = useState<Status | null>(null);
  const [reason, setReason] = useState(
    "По результатам рассмотрения этой демонстрационной заявки кредит не одобрен.",
  );
  if (!a || a.status === "draft") return <Empty title="Досье недоступно" />;
  const q = quote(amount, months, rate);
  const editable = a.status === "review";
  const c = CATALOG[a.product];
  const valid =
    Number.isFinite(amount) &&
    Number.isInteger(months) &&
    amount >= c.min &&
    amount <= c.max &&
    months >= c.minMonths &&
    months <= c.maxMonths &&
    rate > 0 &&
    rate <= 50;
  const act = (status: Status) => {
    let text = "";
    let patch = { ...a };
    if (status === "needs_info") {
      text = "Запрошены дополнительные сведения";
      patch.request = request;
      patch.requestDocCount = a.docs.length;
    }
    if (status === "approved" || status === "alternative") {
      text = "Отправлено предложение, версия " + (a.version + 1);
      patch = {
        ...patch,
        offerAmount: amount,
        offerMonths: months,
        offerRate: rate,
        version: a.version + 1,
        docs: a.docs.map((d) => ({ ...d, status: "accepted" })),
      };
    }
    if (status === "rejected") {
      text = "Отказ подтверждён в демо";
      patch.clientReason = reason;
    }
    if (status === "ready") {
      text = "Готовность к выдаче подтверждена. Выдача ещё не выполнена";
    }
    const ok = change(id, () => transition(patch, status, "bank", text));
    if (ok) {
      setConfirm(null);
      setTab("История");
    }
  };
  return (
    <>
      <Button view="text" size={40} onClick={() => go("/bank")}>
        К очереди заявок
      </Button>
      <Heading
        title={"Заявка № " + id}
        description={a.company + " · " + CATALOG[a.product].name}
        action={<Badge status={a.status} />}
      />
      <div className="dossier-bar">
        <span>
          Ответственный: <strong>{a.owner || "Не назначен"}</strong>
        </span>
        {!a.owner && (
          <Btn
            secondary
            small
            onClick={() =>
              change(id, (v) => ({
                ...v,
                owner: "Екатерина Волкова",
                history: [
                  ...v.history,
                  event(
                    "Заявка назначена Екатерине Волковой",
                    "Сотрудник банка",
                  ),
                ],
              }))
            }
          >
            Взять в работу
          </Btn>
        )}
        <span>Данные синтетические</span>
      </div>
      <Tabs
        items={["Досье", "Документы", "Проверки", "Решение", "История"]}
        value={tab}
        onChange={setTab}
      />
      {tab === "Досье" && (
        <>
          <div className="two-col">
            <Panel>
              <h2>Запрос клиента</h2>
              <Facts
                items={[
                  ["Компания", a.company],
                  ["ИНН", a.inn],
                  ["Сумма / лимит", money(a.amount)],
                  [
                    a.product === "line"
                      ? "Срок первого транша"
                      : "Срок кредита",
                    a.months + " мес.",
                  ],
                  ["Цель", a.goal],
                  ["Источник", "Из демо-заявки клиента"],
                ]}
              />
            </Panel>
            <Panel>
              <h2>Финансовые сведения</h2>
              <p className="muted">Апрель — сентябрь 2026</p>
              <Facts
                items={[
                  [
                    "Выручка",
                    a.revenue ? money(Number(a.revenue)) : "Не указана",
                  ],
                  [
                    "Расходы",
                    a.expenses ? money(Number(a.expenses)) : "Не указаны",
                  ],
                  [
                    "Остаток задолженности",
                    a.debt !== "" ? money(Number(a.debt)) : "Не указан",
                  ],
                  [
                    "Платежи за месяц",
                    a.payment !== "" ? money(Number(a.payment)) : "Не указаны",
                  ],
                ]}
              />
              <Notice>
                Сведения из анкеты. Документы и результаты проверок
                рассматриваются отдельно.
              </Notice>
            </Panel>
          </div>
          <Panel>
            <h2>Внутренний комментарий</h2>
            <Textarea
              block
              label="Комментарий сотрудника"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              hint="Виден только в демонстрационном интерфейсе сотрудника"
            />
            <div className="button-row">
              <Btn
                secondary
                onClick={() =>
                  change(id, (v) => ({
                    ...v,
                    internalComment: comment,
                    history: [
                      ...v.history,
                      {
                        ...event(
                          "Внутренний комментарий сохранён",
                          "Сотрудник банка",
                        ),
                        internal: true,
                      },
                    ],
                  }))
                }
              >
                Сохранить комментарий
              </Btn>
              <Btn onClick={() => setTab("Проверки")}>К проверкам</Btn>
            </div>
          </Panel>
        </>
      )}
      {tab === "Документы" && (
        <Panel>
          <h2>Документы клиента</h2>
          <DocumentList a={a} />
          {editable && (
            <>
              <h2>Запросить сведения</h2>
              <Textarea
                block
                label="Что требуется, период и требования"
                value={request}
                onChange={(e) => setRequest(e.target.value)}
              />
              <p className="fine-print">
                Клиент увидит этот текст в своей заявке.
              </p>
              <Btn
                disabled={!request.trim()}
                onClick={() => setConfirm("needs_info")}
              >
                Отправить запрос
              </Btn>
            </>
          )}
        </Panel>
      )}
      {tab === "Проверки" && (
        <>
          <Panel>
            <h2>Результаты проверок</h2>
            <p className="muted">
              Локальный демонстрационный сценарий. Модель скоринга и внешние
              источники не вызываются.
            </p>
            {[
              "Сведения о компании",
              "Полнота документов",
              "Финансовые показатели",
              "Полномочия участника",
            ].map((t) => (
              <div className="check-row" key={t}>
                <div>
                  <strong>{t}</strong>
                  <small>Источник: синтетический набор</small>
                </div>
                <span className={"badge " + (checkError ? "orange" : "blue")}>
                  {checkError ? "Источник недоступен" : "Требует проверки"}
                </span>
              </div>
            ))}
            <div className="button-row">
              <Button
                view="secondary"
                size={40}
                onClick={() => {
                  setCheckError(!checkError);
                  setChecks(false);
                }}
              >
                {checkError
                  ? "Восстановить демо-источник"
                  : "Показать сбой источника"}
              </Button>
            </div>
            {checkError && (
              <Notice tone="orange">
                Не удалось получить результат проверки. Технический сбой не
                является отказом в кредите. Повторите проверку после
                восстановления источника.
              </Notice>
            )}
            <Checkbox
              checked={checks}
              disabled={checkError}
              onChange={(e) => setChecks(e.target.checked)}
              label="Проверил синтетические документы и сведения"
            />
            <Notice>
              Рекомендация и решение — разные события. В этом сценарии решение
              выбирает сотрудник вручную, без расчёта кредитоспособности.
            </Notice>
            <Btn onClick={() => setTab("Решение")}>Подготовить решение</Btn>
          </Panel>
        </>
      )}
      {tab === "Решение" && (
        <>
          {editable ? (
            <Panel>
              <h2>Подготовить решение</h2>
              <p>
                Проверьте параметры предложения. Решение не запускает выдачу.
              </p>
              <div className="fields three-col">
                <Field
                  label="Сумма / лимит, ₽"
                  type="number"
                  value={amount}
                  min={c.min}
                  max={c.max}
                  onChange={(e) => setAmount(Number(e.target.value))}
                />
                <Field
                  label={
                    a.product === "line"
                      ? "Срок первого транша, месяцев"
                      : "Срок кредита, месяцев"
                  }
                  type="number"
                  value={months}
                  min={c.minMonths}
                  max={c.maxMonths}
                  onChange={(e) => setMonths(Number(e.target.value))}
                />
                <Field
                  label="Ставка, % годовых"
                  type="number"
                  value={rate}
                  onChange={(e) => setRate(Number(e.target.value))}
                />
              </div>
              <Facts
                items={[
                  [
                    "Клиент запрашивал",
                    money(a.amount) + " · " + a.months + " мес.",
                  ],
                  ["Комиссии / обеспечение", "0 ₽ / не требуется в демо"],
                  [
                    a.product === "line"
                      ? "Платёж по траншу"
                      : "Ориентировочный платёж",
                    a.product === "line"
                      ? "Рассчитывается для выбранного транша"
                      : money(q.payment),
                  ],
                ]}
              />
              {(!checks || checkError) && (
                <Notice tone="orange">
                  Перед отправкой завершите проверку на вкладке «Проверки».
                </Notice>
              )}
              {!valid && (
                <p className="field-error">
                  Параметры не входят в диапазон демонстрационного каталога.
                </p>
              )}
              <Btn
                disabled={!valid || !checks || checkError}
                onClick={() =>
                  setConfirm(
                    amount !== a.amount ||
                      months !== a.months ||
                      rate !== a.rate
                      ? "alternative"
                      : "approved",
                  )
                }
              >
                Проверить предложение
              </Btn>
              <div className="divider" />
              <details>
                <summary>Подготовить отказ</summary>
                <p>
                  Клиент увидит только сообщение ниже. Внутренний комментарий
                  ему не отправляется.
                </p>
                <Notice>{reason}</Notice>
                <Btn
                  secondary
                  disabled={!checks || checkError}
                  onClick={() => setConfirm("rejected")}
                >
                  Предпросмотр отказа
                </Btn>
              </details>
            </Panel>
          ) : a.status === "signed" ? (
            <Panel>
              <h2>Проверить готовность к выдаче</h2>
              <Facts
                items={[
                  ["Текущая версия предложения", a.version],
                  ["Подписанная версия", a.signedVersion ?? "Не подписано"],
                  ["Документы", a.docs.length + " файл(ов)"],
                  ["Дополнительные условия", "Не заданы в демо"],
                ]}
              />
              <Checkbox
                label="Проверил подпись текущей версии и документы"
                checked={checks}
                onChange={(e) => setChecks(e.target.checked)}
              />
              <p className="fine-print">
                Подтверждение готовности не перечисляет деньги клиенту.
              </p>
              <Btn
                disabled={!checks || a.signedVersion !== a.version}
                onClick={() => setConfirm("ready")}
              >
                Подтвердить готовность к выдаче
              </Btn>
            </Panel>
          ) : (
            <Panel>
              <h2>Решение и дальнейшие действия</h2>
              <Badge status={a.status} />
              <p>
                {a.status === "needs_info"
                  ? "Ожидаем ответ клиента. После ответа заявка вернётся на рассмотрение."
                  : a.status === "ready"
                    ? "Готовность подтверждена. Клиент может оформить демонстрационную выдачу."
                    : "Решение сохранено в истории. Действие на этом этапе выполняет клиент."}
              </p>
              <Facts
                items={[
                  [
                    "Предложено",
                    a.offerAmount ? money(a.offerAmount) : "Предложения нет",
                  ],
                  ["Версия", a.version],
                ]}
              />
            </Panel>
          )}
        </>
      )}
      {tab === "История" && (
        <Panel>
          <h2>История заявки</h2>
          <History a={a} internal />
        </Panel>
      )}
      {confirm && (
        <Modal
          title={
            confirm === "needs_info"
              ? "Отправить запрос клиенту?"
              : confirm === "rejected"
                ? "Подтвердить отказ в демо?"
                : confirm === "ready"
                  ? "Подтвердить готовность?"
                  : "Отправить предложение в демо?"
          }
          onClose={() => setConfirm(null)}
        >
          <p>
            {confirm === "needs_info"
              ? request
              : confirm === "rejected"
                ? reason
                : confirm === "ready"
                  ? "Готовность будет зафиксирована для версии " +
                    a.version +
                    ". Это действие не перечисляет деньги."
                  : "Клиент увидит " +
                    money(amount) +
                    " на " +
                    months +
                    " мес. по ставке " +
                    rate +
                    "% годовых. Комиссии и услуги — 0 ₽. Версия " +
                    (a.version + 1) +
                    "."}
          </p>
          <Notice>
            Изменение появится в истории той же демонстрационной заявки.
          </Notice>
          <div className="button-row">
            <Btn secondary onClick={() => setConfirm(null)}>
              Вернуться к проверке
            </Btn>
            <Btn onClick={() => act(confirm)}>Подтвердить в демо</Btn>
          </div>
        </Modal>
      )}
    </>
  );
}
