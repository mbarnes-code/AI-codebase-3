import Markdown from 'markdown-to-jsx';
import Alert from '../Alert/Alert';
import React from 'react';

type Props = {
  children: string;
};

const ALERT_TYPE_MAP: Record<string, any> = {
  NOTE: {
    type: 'info',
    icon: 'circleInfo',
    title: 'Note',
  },
  TIP: {
    type: 'success',
    icon: 'lightbulb',
    title: 'Tip',
  },
  IMPORTANT: {
    type: 'important',
    icon: 'star',
    title: 'Important',
  },
  WARNING: {
    type: 'warning',
    icon: 'triangleExclamation',
    title: 'Warning',
  },
  CAUTION: {
    type: 'error',
    icon: 'circleXmark',
    title: 'Caution',
  },
};
const SyntaxMarkdown: React.FC<Props> = ({ children }) => {
  let processedChildren = '';
  let currentAlert = '';
  let alertType = '';
  children.split('\n').forEach((line) => {
    if (alertType && line.startsWith('>')) {
      currentAlert += line.replace('>', '').trim() + '\n';
      return;
    }
    if (alertType && !line.startsWith('>')) {
      processedChildren += `<Alert type="${ALERT_TYPE_MAP[alertType].type}" icon="${ALERT_TYPE_MAP[alertType].icon}" title="${ALERT_TYPE_MAP[alertType].title}">${currentAlert}</Alert>`;
      alertType = '';
      currentAlert = '';
    }
    if (line.startsWith('>')) {
      const matches = line.match(/\[!(.*?)]/);
      const type = matches ? matches[1] : '';
      if (type) {
        alertType = type;
        return;
      }
    }
    processedChildren += line + '\n';
  });

  return (
    <Markdown
      options={{
        overrides: {
          Alert: {
            component: Alert,
          },
        },
      }}
    >
      {processedChildren}
    </Markdown>
  );
};

export default SyntaxMarkdown;
