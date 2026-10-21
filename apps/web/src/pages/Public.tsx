import { useState } from "react";
import {
  Btn,
  Button,
  Field,
  Modal,
  Facts,
  Notice,
  Panel,
  Heading,
  download,
} from "../components/ui";
import { Brand, Icon } from "../components/icons";
import { CATALOG, money, moneyExact, quote, type Product } from "../domain";
import { go, useStore } from "../store";
export const FAQ = [
  [
    "Как узнать точные условия?",
    "Начните с предварительного расчёта. После рассмотрения заявки в кабинете появятся решение и предложение с условиями. В этом прототипе все суммы и тарифы демонстрационные.",
  ],
  [
    "Чем кредит отличается от кредитной линии?",
    "Кредит выдаётся одной суммой. Из линии деньги получают частями — траншами. Возвращённый основной долг восстанавливает доступный лимит по условиям договора.",
  ],
  [
    "Нужно ли заполнять всё сразу?",
    "Нет. Неполная заявка сохраняется в этом браузере. Вернуться к ней можно в разделе «Заявки».",
  ],
  [
    "Может ли бухгалтер подготовить заявку?",
    "Да. Бухгалтер заполняет сведения и добавляет документы. Отправка заявки и подписание доступны руководителю в соответствующей демонстрационной роли.",
  ],
  [
    "Можно ли вернуть деньги раньше?",
    "Откройте «Досрочное погашение» в карточке кредита. Сначала вы увидите расчёт и изменение графика, затем сможете подтвердить демонстрационную операцию.",
  ],
];
export function PublicHeader() {
  const [menu, setMenu] = useState(false);
  return (
    <header className="public-header">
      <div className="container header-inner">
        <Brand dark />
        <nav
          className={menu ? "public-nav open" : "public-nav"}
          aria-label="Основная навигация"
        >
          <a href="#/products" onClick={() => setMenu(false)}>
            Финансирование
          </a>
          <a href="#/calculator" onClick={() => setMenu(false)}>
            Калькулятор
          </a>
          <a href="#/help" onClick={() => setMenu(false)}>
            Помощь
          </a>
        </nav>
        <div className="header-actions">
          <span className="demo-label">Демо</span>
          <Button
            view="secondary"
            colors="inverted"
            size={40}
            onClick={() => go("/login")}
          >
            Войти в кабинет
          </Button>
          <Button
            view="transparent"
            colors="inverted"
            size={40}
            className="mobile-menu"
            aria-expanded={menu}
            aria-label="Меню"
            onClick={() => setMenu(!menu)}
          >
            ☰
          </Button>
        </div>
      </div>
    </header>
  );
}
export function Footer() {
  return (
    <footer className="public-footer container">
      <div className="footer-top">
        <Brand />
        <div>
          <a href="#/products">Условия продуктов</a>
          <a href="#/help">Помощь</a>
          <a href="#/login/bank">Сотрудникам банка</a>
        </div>
      </div>
      <p>
        Демонстрационный проект команды SYNAPTIX. Компании, документы и условия
        вымышлены. Заявки не поступают в банк, подпись имитируется, деньги не
        выдаются. Не вводите настоящие данные.
      </p>
      <div className="footer-bottom">
        <span>Кредитный кабинет · 2026</span>
        <span>Данные сценария хранятся в вашем браузере</span>
      </div>
    </footer>
  );
}
export function Home() {
  return (
    <div className="marketing">
      <PublicHeader />
      <main>
        <div className="hero-wrap">
          <section className="hero container">
            <div className="hero-copy">
              <p className="eyebrow">Кредитный кабинет для бизнеса</p>
              <h1>
                Кредит под
                <br />
                вашу задачу
              </h1>
              <p className="hero-description">
                На закупки, оборудование или оплату расходов.
                <br className="desktop-only" /> Рассчитайте платёж и оформите
                заявку в кабинете.
              </p>
              <Btn onClick={() => go("/calculator")}>Подобрать кредит</Btn>
              <div className="hero-proof">
                <span>
                  <Icon name="check" />
                  Расчёт до заявки
                </span>
                <span>
                  <Icon name="check" />
                  Всё онлайн
                </span>
              </div>
            </div>
            <div className="hero-visual">
              <img
                src="/assets/business-store.png"
                alt="Бирюзовый магазин с красными коробками и платёжным терминалом"
                loading="eager"
              />
              <div className="glass-label">
                <Icon name="business" />
                <div>
                  <strong>Ваш бизнес. Ваши планы.</strong>
                  <span>Финансирование — в одном кабинете</span>
                </div>
              </div>
            </div>
          </section>
          <div className="container hero-bottom">
            <span>01 / Выберите задачу</span>
            <span>02 / Рассчитайте платёж</span>
            <span>03 / Отправьте заявку</span>
          </div>
        </div>
        <div className="white-sheet">
          <section className="container section">
            <div className="section-heading">
              <h2>На что нужны деньги</h2>
              <p>
                Для большого шага и ежедневных дел.
                <br />
                Выберите задачу — начнём с неё.
              </p>
            </div>
            <div className="task-grid">
              <article className="task-card task-large turquoise">
                <div>
                  <span className="eyebrow">Закупки и оборотные средства</span>
                  <h3>
                    Чтобы на полках
                    <br />
                    было всё нужное
                  </h3>
                  <p>
                    Пополнить склад, купить сырьё
                    <br />
                    или материалы.
                  </p>
                  <Btn secondary onClick={() => go("/calculator?goal=stock")}>
                    Рассчитать кредит
                  </Btn>
                </div>
                <img
                  src="/assets/business-store.png"
                  alt="Магазин и поставка товаров"
                  loading="lazy"
                />
              </article>
              <article className="task-card equipment-card">
                <h3>
                  Обновить
                  <br />
                  оборудование
                </h3>
                <p>
                  Для техники, которая
                  <br />
                  работает на ваш бизнес.
                </p>
                <img
                  src="/assets/equipment.png"
                  alt="Бирюзовая кофемашина с красной чашкой"
                  loading="lazy"
                />
                <Button
                  view="primary"
                  size={40}
                  onClick={() => go("/calculator?goal=equipment")}
                >
                  Посмотреть условия
                </Button>
              </article>
              <article className="task-card small-task peach">
                <Icon name="document" />
                <div>
                  <h3>Выполнить заказ</h3>
                  <p>Оплатить расходы до поступления денег от заказчика.</p>
                </div>
                <Button
                  view="transparent"
                  size={40}
                  aria-label="Рассчитать финансирование заказа"
                  onClick={() => go("/calculator?goal=order")}
                >
                  <Icon name="right" />
                </Button>
              </article>
              <article className="task-card small-task lavender">
                <Icon name="calendar" />
                <div>
                  <h3>Покрыть текущие расходы</h3>
                  <p>На аренду, поставки и другие задачи бизнеса.</p>
                </div>
                <Button
                  view="transparent"
                  size={40}
                  aria-label="Рассчитать текущие расходы"
                  onClick={() => go("/calculator?goal=current")}
                >
                  <Icon name="right" />
                </Button>
              </article>
            </div>
          </section>
          <section className="container section" id="products">
            <div className="section-heading">
              <h2>
                Одной суммой
                <br />
                или частями
              </h2>
              <p>
                Разная механика — под разные задачи.
                <br />
                Сравните, как получать и возвращать деньги.
              </p>
            </div>
            <ProductCards />
          </section>
          <section className="calc-section">
            <div className="container section">
              <div className="section-heading">
                <h2>
                  Посмотрите, каким
                  <br />
                  будет платёж
                </h2>
                <p>
                  Сумма, срок и все расходы.
                  <br />
                  Рассчитайте до оформления заявки.
                </p>
              </div>
              <Calculator embedded />
            </div>
          </section>
          <section className="container section">
            <div className="section-heading">
              <h2>
                От расчёта до выдачи —<br />в кабинете
              </h2>
              <p>
                Статус, документы и следующий шаг
                <br />
                всегда перед вами.
              </p>
            </div>
            <div className="steps-grid">
              {[
                ["Выберите условия", "Укажите задачу, сумму и срок."],
                [
                  "Отправьте заявку",
                  "Проверьте сведения и добавьте документы.",
                ],
                [
                  "Посмотрите решение",
                  "Ответьте на запрос или изучите предложение.",
                ],
                ["Оформите выдачу", "Подпишите документы и выполните условия."],
              ].map(([t, d], i) => (
                <article key={t}>
                  <span className="step-number">0{i + 1}</span>
                  <h3>{t}</h3>
                  <p>{d}</p>
                </article>
              ))}
            </div>
          </section>
          <section className="container section">
            <div className="cabinet-promo">
              <div>
                <p className="eyebrow">Кредитный кабинет</p>
                <h2>
                  Продолжим
                  <br />с того же места
                </h2>
                <p>
                  Сохраняйте заявку, следите за решением
                  <br />и планируйте платежи. Всё по кредиту — здесь.
                </p>
                <Button
                  view="secondary"
                  colors="inverted"
                  size={56}
                  onClick={() => go("/login")}
                >
                  Посмотреть кабинет
                </Button>
              </div>
              <div
                className="cabinet-preview"
                aria-label="Пример интерфейса кабинета"
              >
                <div className="preview-top">
                  <span>Обзор</span>
                  <span className="mini-logo">Альфа-Банк</span>
                </div>
                <div className="preview-alert">
                  <span className="badge green">Условия готовы</span>
                  <h3>Проверьте предложение</h3>
                  <p>Заявка на 1 500 000 ₽</p>
                  <div className="preview-button">Посмотреть условия</div>
                </div>
                <div className="preview-bottom">
                  <div>
                    <Icon name="calendar" />
                    <strong>Платежи</strong>
                    <span>По вашему графику</span>
                  </div>
                  <div>
                    <Icon name="document" />
                    <strong>Документы</strong>
                    <span>Всегда под рукой</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
          <section className="container section requirements-grid">
            <div>
              <h2>
                Что понадобится
                <br />
                для заявки
              </h2>
              <p>
                Подготовьте сведения о бизнесе.
                <br />
                Нужные документы подскажем в заявке.
              </p>
            </div>
            <div>
              {[
                "Данные компании или ИП",
                "Выручка и расходы за 6 месяцев",
                "Действующие кредиты и займы",
                "Документы из списка заявки",
                "Сведения об участниках",
              ].map((t, i) => (
                <div className="requirement" key={t}>
                  <span>0{i + 1}</span>
                  <h3>{t}</h3>
                  <Icon name="check" />
                </div>
              ))}
            </div>
          </section>
          <section className="container section faq-section">
            <h2>Вопросы и ответы</h2>
            <FAQList />
          </section>
          <section className="container section">
            <div className="final-promo">
              <div>
                <h2>Начните с расчёта</h2>
                <p>
                  Укажите задачу и сумму. Посмотрите условия
                  <br />
                  перед оформлением заявки.
                </p>
                <Btn onClick={() => go("/calculator")}>Подобрать кредит</Btn>
              </div>
              <img
                src="/assets/equipment.png"
                alt="Кофемашина для нового оборудования бизнеса"
                loading="lazy"
              />
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}
export function FAQList() {
  return (
    <div className="faq-list">
      {FAQ.map(([q, a]) => (
        <details key={q}>
          <summary>
            {q}
            <span>+</span>
          </summary>
          <p>{a}</p>
        </details>
      ))}
    </div>
  );
}
export function ProductCards() {
  return (
    <div className="product-grid">
      <article className="product-card">
        <div className="product-icon">
          <Icon name="wallet" />
        </div>
        <p className="eyebrow">Одной суммой</p>
        <h3>Кредит для бизнеса</h3>
        <p>Получите всю сумму сразу и возвращайте деньги по графику.</p>
        <div className="product-metrics">
          <div>
            <strong>до 5 млн ₽</strong>
            <span>сумма кредита</span>
          </div>
          <div>
            <strong>до 3 лет</strong>
            <span>срок кредита</span>
          </div>
        </div>
        <Btn secondary onClick={() => go("/calculator?product=loan")}>
          Рассчитать кредит
        </Btn>
        <small>Демонстрационные параметры, не тариф банка</small>
      </article>
      <article className="product-card">
        <div className="product-icon red">
          <Icon name="business" />
        </div>
        <p className="eyebrow">Частями</p>
        <h3>Кредитная линия</h3>
        <p>
          Берите деньги, когда они нужны. Погашение основного долга
          восстанавливает лимит.
        </p>
        <div className="product-metrics">
          <div>
            <strong>до 10 млн ₽</strong>
            <span>лимит линии</span>
          </div>
          <div>
            <strong>до 12 мес.</strong>
            <span>срок транша</span>
          </div>
        </div>
        <Btn secondary onClick={() => go("/calculator?product=line")}>
          Рассчитать линию
        </Btn>
        <small>Демонстрационные параметры, не тариф банка</small>
      </article>
    </div>
  );
}
export function ScheduleModal({
  amount,
  months,
  rate,
  onClose,
}: {
  amount: number;
  months: number;
  rate: number;
  onClose: () => void;
}) {
  const q = quote(amount, months, rate);
  return (
    <Modal title="Предварительный график" onClose={onClose}>
      <p className="muted">
        Аннуитетный расчёт, {rate}% годовых. Комиссии в демо — 0 ₽. Даты
        отсчитываются от 21 октября 2026 года.
      </p>
      <div className="table-scroll schedule-table">
        <table>
          <thead>
            <tr>
              <th>Дата</th>
              <th>Основной долг</th>
              <th>Проценты</th>
              <th>Платёж</th>
              <th>Остаток</th>
            </tr>
          </thead>
          <tbody>
            {q.rows.map((r) => (
              <tr key={r.n}>
                <td>{new Date(r.date).toLocaleDateString("ru-RU")}</td>
                <td>{moneyExact(r.principal)}</td>
                <td>{moneyExact(r.interest)}</td>
                <td>{moneyExact(r.total)}</td>
                <td>{moneyExact(r.balance)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Facts
        items={[
          ["Всего выплат", moneyExact(q.total)],
          ["Проценты за срок", moneyExact(q.interest)],
        ]}
      />
      <Btn
        secondary
        onClick={() =>
          download(
            "demo-payment-schedule.csv",
            "Дата;Основной долг;Проценты;Платёж;Остаток\n" +
              q.rows
                .map((r) =>
                  [r.date, r.principal, r.interest, r.total, r.balance].join(
                    ";",
                  ),
                )
                .join("\n"),
            "text/csv;charset=utf-8",
          )
        }
      >
        Скачать график
      </Btn>
    </Modal>
  );
}
export function Calculator({ embedded = false }: { embedded?: boolean }) {
  const { state, login, newApplication } = useStore();
  const params = new URLSearchParams(location.hash.split("?")[1] || "");
  const initial = params.get("product") === "line" ? "line" : "loan";
  const [product, setProduct] = useState<Product>(initial);
  const [amount, setAmount] = useState(1500000);
  const [months, setMonths] = useState(initial === "line" ? 6 : 24);
  const [draw, setDraw] = useState(500000);
  const [show, setShow] = useState(false);
  const [goal, setGoal] = useState(
    (
      {
        stock: "Закупка товара и материалов",
        equipment: "Покупка оборудования",
        order: "Расходы по заказу",
        current: "Текущие расходы",
      } as Record<string, string>
    )[params.get("goal") || ""] || "Закупка товара и материалов",
  );
  const c = CATALOG[product];
  const valid =
    Number.isFinite(amount) &&
    Number.isInteger(months) &&
    amount >= c.min &&
    amount <= c.max &&
    months >= c.minMonths &&
    months <= c.maxMonths &&
    (product === "loan" || (draw > 0 && draw <= amount));
  const q = quote(product === "line" ? draw : amount, months, c.rate);
  const start = () => {
    if (!state.role || state.role === "bank") login("director");
    const id = newApplication(
      product,
      amount,
      months,
      goal,
      product === "line" ? draw : undefined,
    );
    if (id) go("/apply/" + id);
  };
  return (
    <div className="calculator">
      <div className="calc-controls">
        <div className="segmented" aria-label="Способ получения">
          {(["loan", "line"] as const).map((p) => (
            <Button
              size={40}
              view={product === p ? "primary" : "transparent"}
              key={p}
              onClick={() => {
                setProduct(p);
                setAmount(1500000);
                setMonths(p === "line" ? 6 : 24);
              }}
            >
              {p === "loan" ? "Одной суммой" : "Частями"}
            </Button>
          ))}
        </div>
        {!embedded && (
          <label className="select-label">
            На что нужны деньги
            <select value={goal} onChange={(e) => setGoal(e.target.value)}>
              {[
                "Закупка товара и материалов",
                "Покупка оборудования",
                "Расходы по заказу",
                "Текущие расходы",
                "Другая задача",
              ].map((g) => (
                <option key={g}>{g}</option>
              ))}
            </select>
          </label>
        )}
        <div className="range-field">
          <Field
            label={
              product === "line" ? "Лимит кредитной линии" : "Сумма кредита"
            }
            type="number"
            value={amount}
            min={c.min}
            max={c.max}
            onChange={(e) => setAmount(Number(e.target.value))}
            rightAddons={<span>₽</span>}
          />
          <input
            aria-label="Сумма — ползунок"
            type="range"
            min={c.min}
            max={c.max}
            step={100000}
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
          />
          <div className="range-bounds">
            <span>{money(c.min)}</span>
            <span>{money(c.max)}</span>
          </div>
        </div>
        {product === "line" && (
          <Field
            label="Сумма первого транша"
            type="number"
            value={draw}
            onChange={(e) => setDraw(Number(e.target.value))}
            min={1}
            max={amount}
            hint="Расчёт платежей только для этой части лимита"
          />
        )}
        <div className="range-field">
          <Field
            label={
              product === "line"
                ? "Срок первого транша, месяцев"
                : "Срок кредита, месяцев"
            }
            type="number"
            value={months}
            min={c.minMonths}
            max={c.maxMonths}
            onChange={(e) => setMonths(Number(e.target.value))}
          />
          <input
            aria-label="Срок — ползунок"
            type="range"
            min={c.minMonths}
            max={c.maxMonths}
            value={months}
            onChange={(e) => setMonths(Number(e.target.value))}
          />
          <div className="range-bounds">
            <span>{c.minMonths} мес.</span>
            <span>{c.maxMonths} мес.</span>
          </div>
        </div>
        <p className="fine-print">
          Демо-условия для знакомства с кабинетом. Без дополнительных услуг и
          комиссий. Окончательное предложение формируется после рассмотрения.
        </p>
      </div>
      <div className="calc-result">
        <p className="eyebrow">
          {product === "line"
            ? "Расчёт первого транша"
            : "Предварительный расчёт"}
        </p>
        <span className="muted">Ориентировочный платёж в месяц</span>
        <div className="payment-number">{valid ? money(q.payment) : "—"}</div>
        <Facts
          items={[
            ["Ставка для расчёта", c.rate + "% годовых"],
            ["Проценты за выбранный срок", valid ? money(q.interest) : "—"],
            ["Комиссии и услуги", "0 ₽"],
            ["Всего выплат по графику", valid ? money(q.total) : "—"],
          ]}
        />
        {product === "line" && (
          <p className="fine-print">
            Будущие транши не включены. Комиссия за обслуживание линии в демо —
            0 ₽. Срок линии — 24 месяца.
          </p>
        )}
        {!valid && (
          <p role="alert" className="field-error">
            Проверьте диапазон суммы и срока. Транш не может превышать лимит.
          </p>
        )}
        <Btn block disabled={!valid} onClick={start}>
          Перейти к заявке
        </Btn>
        <Button
          view="transparent"
          size={40}
          block
          disabled={!valid}
          onClick={() => setShow(true)}
        >
          Посмотреть график
        </Button>
      </div>
      {show && (
        <ScheduleModal
          amount={product === "line" ? draw : amount}
          months={months}
          rate={c.rate}
          onClose={() => setShow(false)}
        />
      )}
    </div>
  );
}
export function Products() {
  return (
    <>
      <Heading
        title="Финансирование для бизнеса"
        description="Выберите задачу и способ получения денег"
      />
      <ProductCards />
      <Panel>
        <h2>Сравните механику</h2>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Параметр</th>
                <th>Кредит</th>
                <th>Кредитная линия</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Как получить</td>
                <td>Всю сумму сразу</td>
                <td>Частями — траншами</td>
              </tr>
              <tr>
                <td>На что начисляются проценты</td>
                <td>На остаток выданного долга</td>
                <td>На остатки выданных траншей</td>
              </tr>
              <tr>
                <td>Повторное использование</td>
                <td>Новая заявка</td>
                <td>В пределах восстановленного лимита</td>
              </tr>
            </tbody>
          </table>
        </div>
        <Notice>
          Это сравнение двух демонстрационных продуктов. Условия реального
          договора могут отличаться.
        </Notice>
      </Panel>
    </>
  );
}
