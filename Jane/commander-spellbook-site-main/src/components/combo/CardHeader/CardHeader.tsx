import React from 'react';
import styles from './cardHeader.module.scss';

type Props = {
  title?: string;
  subtitle?: string;
  cardsArt?: string[];
};

const CardHeader: React.FC<Props> = ({ title = '', subtitle = '', cardsArt = [] }) => {
  return (
    <header className={`hidden sm:flex ${styles.header}`}>
      <div className="flex w-full h-64">
        {cardsArt.map((cardArt, index) => (
          <img
            alt="Card art"
            src={cardArt}
            key={index}
            className={styles.cardWrapper}
            // style={{ backgroundImage: `url(${encodeURI(cardArt)})` }}
          />
        ))}
      </div>
      <div className={styles.mask} />
      <div className={styles.comboTitleWrapper}>
        <h1 className={`heading-title ${styles.headingTitle} ${styles.comboTitle}`}>{title}</h1>
        <h2 className={`heading-title ${styles.headingTitle} ${styles.comboSubtitle}`}>{subtitle}</h2>
      </div>
    </header>
  );
};

export default CardHeader;
