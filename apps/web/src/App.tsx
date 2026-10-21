import { useEffect, useState, type ReactNode } from "react";
import { Btn, Button, Modal, Notice, Heading, Panel } from "./components/ui";
import { Brand, Icon } from "./components/icons";
import { useStore, useRoute, go } from "./store";
import {
  Home,
  PublicHeader,
  Footer,
  Products,
  Calculator,
} from "./pages/Public";
import {
  Overview,
  Financing,
  Credit,
  Draw,
  Payments,
  Repayment,
} from "./pages/Servicing";
import {
  Applications,
  ApplicationForm,
  ApplicationDetail,
  Offer,
  Signing,
} from "./pages/Applications";
import { BankDossier } from "./pages/Bank";
import {
  Company,
  Documents,
  Help,
  Materials,
  Notifications,
} from "./pages/Workspace";
import type { Role } from "./domain";
function Login() {
  const { login } = useStore();
  const choose = (role: Role) => {
    login(role);
    go(role === "bank" ? "/bank" : "/overview");
  };
  return (
    <div className="login-page">
      <PublicHeader />
      <main className="login-main container">
        <div>
          <p className="eyebrow">Кредитный кабинет</p>
          <h1>
            Ваши планы.
            <br />
            Следующий шаг.
          </h1>
          <p>
            Подберите финансирование, продолжите заявку
            <br />
            или проверьте платежи.
          </p>
          <img
            src="/assets/business-store.png"
            alt="Магазин и поставка товаров"
          />
        </div>
        <Panel className="login-panel">
          <span className="demo-label">Демо</span>
          <h2>Выберите роль</h2>
          <p className="muted">Один кредитный процесс — с двух сторон.</p>
          <Button
            className="role-card"
            block
            size={72}
            view="secondary"
            onClick={() => choose("director")}
          >
            <span className="role-icon">
              <Icon name="business" />
            </span>
            <span>
              <strong>Предприниматель</strong>
              <small>Руководитель · заявка, условия и подпись</small>
            </span>
            <Icon name="right" />
          </Button>
          <Button
            className="role-card"
            block
            size={72}
            view="secondary"
            onClick={() => choose("accountant")}
          >
            <span className="role-icon">
              <Icon name="document" />
            </span>
            <span>
              <strong>Бухгалтер</strong>
              <small>Подготовка заявки и документов</small>
            </span>
            <Icon name="right" />
          </Button>
          <div className="divider" />
          <Button
            className="role-card"
            block
            size={72}
            view="secondary"
            onClick={() => choose("bank")}
          >
            <span className="role-icon bank">
              <Icon name="wallet" />
            </span>
            <span>
              <strong>Сотрудник банка</strong>
              <small>Очередь, проверка и решение</small>
            </span>
            <Icon name="right" />
          </Button>
          <p className="fine-print">
            Компании и условия вымышлены. Настоящие данные не нужны. Выбор роли
            моделирует интерфейс, не создаёт банковскую учётную запись.
          </p>
        </Panel>
      </main>
    </div>
  );
}
const nav = [
  ["/overview", "Обзор", "home"],
  ["/financing", "Финансирование", "wallet"],
  ["/applications", "Заявки", "business"],
  ["/documents", "Документы", "document"],
] as const;
function Shell({ children, path }: { children: ReactNode; path: string }) {
  const { state, update, reset } = useStore();
  const [menu, setMenu] = useState(false);
  const [demo, setDemo] = useState(false);
  const [resetConfirm, setResetConfirm] = useState(false);
  const bank = state.role === "bank";
  useEffect(() => setMenu(false), [path]);
  const items = bank
    ? ([
        ["/bank", "Очередь заявок", "business"],
        ["/bank/help", "Обращения", "help"],
      ] as const)
    : nav;
  return (
    <div className="app-shell">
      <aside className={"sidebar " + (menu ? "open" : "")}>
        <Brand />
        <p className="workspace-label">
          {bank ? "Рабочее место сотрудника" : "Кредитный кабинет"}
        </p>
        <nav aria-label="Разделы кабинета">
          {items.map(([href, text, icon]) => (
            <a
              key={href}
              href={"#" + href}
              className={
                (
                  href === "/bank"
                    ? path === "/bank" || path.startsWith("/bank/application")
                    : path.startsWith(href)
                )
                  ? "active"
                  : ""
              }
            >
              <Icon name={icon} />
              {text}
            </a>
          ))}
        </nav>
        {!bank && (
          <div className="side-secondary">
            <a href="#/payments">
              <Icon name="calendar" />
              Платёжный календарь
            </a>
            <a href="#/company">
              <Icon name="business" />
              Компания и доступ
            </a>
            <a href="#/materials">
              <Icon name="document" />
              Полезное для бизнеса
            </a>
          </div>
        )}
        <div className="sidebar-bottom">
          <a href={bank ? "#/bank/help" : "#/help"}>
            <Icon name="help" />
            Помощь
          </a>
          <a href="#/login">
            <Icon name="exit" />
            Сменить роль
          </a>
          <div className="sidebar-demo">
            <Button view="transparent" size={32} onClick={() => setDemo(true)}>
              Демо-сценарий
            </Button>
            <span>SYNAPTIX · 2026</span>
          </div>
        </div>
      </aside>
      {menu && (
        <button
          className="menu-scrim"
          aria-label="Закрыть меню"
          onClick={() => setMenu(false)}
        />
      )}
      <div className="workspace">
        <header className="workspace-header">
          <Button
            className="mobile-menu"
            view="transparent"
            size={40}
            aria-label="Открыть меню кабинета"
            aria-expanded={menu}
            onClick={() => setMenu(!menu)}
          >
            ☰
          </Button>
          <a href={bank ? "#/bank" : "#/company"} className="company-switch">
            <span className="company-icon">{bank ? "А" : "М"}</span>
            <span>
              <strong>{bank ? "Кредитование бизнеса" : "ООО «Маяк»"}</strong>
              <small>
                {bank
                  ? "Екатерина Волкова · сотрудник"
                  : state.role === "director"
                    ? "Александр Смирнов · руководитель"
                    : "Мария Кузнецова · бухгалтер"}
              </small>
            </span>
          </a>
          <div className="header-actions">
            <Button
              view="transparent"
              size={32}
              className="demo-label"
              onClick={() => setDemo(true)}
            >
              Демо
            </Button>
            {!bank && (
              <Button
                view="transparent"
                size={40}
                aria-label="Уведомления"
                onClick={() => go("/notifications")}
              >
                <Icon name="bell" />
              </Button>
            )}
            <span className="user-avatar">
              {bank ? "ЕВ" : state.role === "director" ? "АС" : "МК"}
            </span>
          </div>
        </header>
        <main className="workspace-main" id="main-content" tabIndex={-1}>
          {children}
        </main>
        <footer className="workspace-footer">
          <span>Демонстрационный кабинет · Только синтетические данные</span>
          <a href="#/">На главную</a>
        </footer>
      </div>
      {demo && (
        <Modal
          title="Сценарий демонстрации"
          onClose={() => {
            setDemo(false);
            setResetConfirm(false);
          }}
        >
          <Notice>
            Компании, документы и условия вымышлены. Заявки не поступают в банк,
            подпись имитируется, деньги не выдаются. Состояние сохраняется
            только в этом браузере.
          </Notice>
          <h3>Проверьте весь путь</h3>
          <ol className="scenario-list">
            <li>Рассчитайте и заполните заявку</li>
            <li>Смените роль на сотрудника банка</li>
            <li>Откройте досье, проверьте сведения, отправьте предложение</li>
            <li>Вернитесь к руководителю и подпишите документы</li>
            <li>
              Подтвердите готовность сотрудником, затем оформите выдачу клиентом
            </li>
          </ol>
          <div className="button-row">
            <Btn
              secondary
              onClick={() => {
                setDemo(false);
                go("/login");
              }}
            >
              Сменить роль
            </Btn>
            <Button view="text" size={40} onClick={() => setResetConfirm(true)}>
              Начать заново
            </Button>
          </div>
          {resetConfirm && (
            <Notice tone="orange">
              <p>
                Текущие демо-заявки и изменения будут заменены исходным набором.
              </p>
              <Btn
                small
                onClick={() => {
                  reset();
                  setDemo(false);
                  setResetConfirm(false);
                  go(bank ? "/bank" : "/overview");
                }}
              >
                Подтвердить сброс сценария
              </Btn>
            </Notice>
          )}
        </Modal>
      )}
    </div>
  );
}
export default function App() {
  const route = useRoute();
  const { state } = useStore();
  const path = route.split("?")[0];
  const id = decodeURIComponent(path.split("/").filter(Boolean).at(-1) || "");
  useEffect(() => {
    const titles: Record<string, string> = {
      "/": "Кредит под вашу задачу",
      "/overview": "Обзор",
      "/bank": "Заявки на финансирование",
      "/calculator": "Расчёт кредита",
      "/applications": "Заявки",
    };
    document.title = (titles[path] || "Кредитный кабинет") + " · Альфа · Демо";
  }, [path]);
  if (path === "/") return <Home />;
  if (path.startsWith("/login")) return <Login />;
  let content: ReactNode;
  if (path === "/products") content = <Products />;
  else if (path === "/calculator")
    content = (
      <>
        <Heading
          title="Рассчитайте финансирование"
          description="Сначала параметры и стоимость. Затем — заявка."
        />
        <Calculator />
      </>
    );
  else if (path === "/help") content = <Help />;
  else if (!state.role) return <Login />;
  else if (path.startsWith("/bank") && state.role !== "bank")
    content = (
      <Panel>
        <h1>Рабочее место сотрудника</h1>
        <p>Выберите демонстрационную роль сотрудника банка.</p>
        <Btn onClick={() => go("/login")}>Выбрать роль</Btn>
      </Panel>
    );
  else if (path === "/bank") content = <Applications bank />;
  else if (path === "/bank/help") content = <Help bank />;
  else if (path.startsWith("/bank/application/"))
    content = <BankDossier key={id} id={id} />;
  else if (state.role === "bank")
    content = (
      <Panel>
        <h1>Кабинет предпринимателя</h1>
        <p>Для этого экрана выберите роль руководителя или бухгалтера.</p>
        <Btn onClick={() => go("/login")}>Выбрать роль</Btn>
      </Panel>
    );
  else if (path === "/overview") content = <Overview />;
  else if (path === "/financing") content = <Financing />;
  else if (path === "/applications") content = <Applications />;
  else if (path.startsWith("/apply/"))
    content = <ApplicationForm key={id} id={id} />;
  else if (path.startsWith("/application/"))
    content = <ApplicationDetail key={id} id={id} />;
  else if (path.startsWith("/offer/")) content = <Offer key={id} id={id} />;
  else if (path.startsWith("/sign/")) content = <Signing key={id} id={id} />;
  else if (path.startsWith("/credit/")) content = <Credit key={id} id={id} />;
  else if (path.startsWith("/draw/")) content = <Draw key={id} id={id} />;
  else if (path.startsWith("/repay/")) content = <Repayment key={id} id={id} />;
  else if (path === "/payments") content = <Payments />;
  else if (path === "/documents") content = <Documents />;
  else if (path === "/company") content = <Company />;
  else if (path === "/notifications") content = <Notifications />;
  else if (path.startsWith("/materials"))
    content = <Materials id={path === "/materials" ? undefined : id} />;
  else
    content = (
      <Panel>
        <h1>Такой страницы нет</h1>
        <p>Проверьте адрес или вернитесь к обзору.</p>
        <Btn onClick={() => go("/overview")}>К обзору</Btn>
      </Panel>
    );
  return (
    <>
      <a
        className="skip-link"
        href="#main-content"
        onClick={(e) => {
          e.preventDefault();
          const main = document.getElementById("main-content");
          main?.focus();
          main?.scrollIntoView();
        }}
      >
        К содержимому
      </a>
      {state.role ? (
        <Shell path={path}>{content}</Shell>
      ) : (
        <div className="marketing">
          <PublicHeader />
          <main
            className="container public-content"
            id="main-content"
            tabIndex={-1}
          >
            {content}
          </main>
          <Footer />
        </div>
      )}
    </>
  );
}
