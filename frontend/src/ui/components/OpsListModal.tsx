import { ReactNode } from 'react';
import { X } from 'lucide-react';

interface OpsListModalProps {
  isOpen: boolean;
  title: string;
  subtitle: string;
  children: ReactNode;
  onClose: () => void;
}

export function OpsListModal({ isOpen, title, subtitle, children, onClose }: OpsListModalProps) {
  if (!isOpen) return null;

  return (
    <div className="ops-list-modal-backdrop" role="presentation">
      <section className="ops-list-modal" role="dialog" aria-modal="true" aria-label={title}>
        <header>
          <div>
            <span>Scrollable records</span>
            <h3>{title}</h3>
            <p>{subtitle}</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close list">
            <X size={18} />
          </button>
        </header>
        <div className="ops-list-modal__body">
          {children}
        </div>
      </section>
    </div>
  );
}
