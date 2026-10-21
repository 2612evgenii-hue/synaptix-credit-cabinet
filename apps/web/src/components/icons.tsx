import { HouseMIcon } from "@alfalab/icons-glyph/HouseMIcon";
import { WalletMIcon } from "@alfalab/icons-glyph/WalletMIcon";
import { DocumentMIcon } from "@alfalab/icons-glyph/DocumentMIcon";
import { BriefcaseMIcon } from "@alfalab/icons-glyph/BriefcaseMIcon";
import { BellMIcon } from "@alfalab/icons-glyph/BellMIcon";
import { CalendarLineMIcon } from "@alfalab/icons-glyph/CalendarLineMIcon";
import { QuestionCircleMIcon } from "@alfalab/icons-glyph/QuestionCircleMIcon";
import { CheckmarkHeavyMIcon } from "@alfalab/icons-glyph/CheckmarkHeavyMIcon";
import { ChevronRightMIcon } from "@alfalab/icons-glyph/ChevronRightMIcon";
import { ArrowLeftMIcon } from "@alfalab/icons-glyph/ArrowLeftMIcon";
import { LogOutMIcon } from "@alfalab/icons-glyph/LogOutMIcon";
import { AlfaBankLIcon } from "@alfalab/icons-logotype/AlfaBankLIcon";
const icons = {
  home: HouseMIcon,
  wallet: WalletMIcon,
  document: DocumentMIcon,
  business: BriefcaseMIcon,
  bell: BellMIcon,
  calendar: CalendarLineMIcon,
  help: QuestionCircleMIcon,
  check: CheckmarkHeavyMIcon,
  right: ChevronRightMIcon,
  back: ArrowLeftMIcon,
  exit: LogOutMIcon,
};
export function Icon({
  name,
  className = "",
}: {
  name: keyof typeof icons;
  className?: string;
}) {
  const C = icons[name];
  return <C aria-hidden className={className} />;
}
export function Brand({ dark = false }: { dark?: boolean }) {
  return (
    <a
      className={"brand " + (dark ? "brand-light" : "")}
      href="#/"
      aria-label="Альфа-Банк — главная демо-кабинета"
    >
      <AlfaBankLIcon aria-hidden />
      <span>
        Альфа-Банк<small>ДЛЯ БИЗНЕСА</small>
      </span>
    </a>
  );
}
