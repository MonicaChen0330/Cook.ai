import './InfoBlock.css';

// 這個元件接收標題(title)和項目列表(items)作為 props
function InfoBlock({ title, items }) {
  return (
    <div className="dashboard-block">
      <h3 className="block-title">{title}</h3>
        {items.length > 0 && (
        <ul className="info-block-list">
          {items.map((item, index) => (
            <li key={index}>
              <a href="#">{item.text}</a>
              {item.isNew && <span className="new-badge">NEW</span>}
            </li>
          ))}
        </ul>
      )}

      {items.length === 0 && (
        <p className="no-items">目前沒有新項目</p>
      )}
    </div>
  );
}

export default InfoBlock;