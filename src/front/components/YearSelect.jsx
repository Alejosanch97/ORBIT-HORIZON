import React from 'react';
import useGlobalReducer from '../hooks/useGlobalReducer';
import { getCurrentYear, getViewYear, getYearOptions } from '../schoolYear';

/* Selector de año escolar. Comparte el estado global (store.viewYear),
   así que cambiarlo en una pantalla cambia el año en todas. */
export const YearSelect = ({ className = 'pl-select', style }) => {
    const { store, dispatch } = useGlobalReducer();
    const current = getCurrentYear(store);
    const value = getViewYear(store);

    return (
        <select
            className={className}
            style={style}
            value={value}
            title="Año escolar"
            onChange={(e) => dispatch({ type: 'set_view_year', payload: Number(e.target.value) })}
        >
            {getYearOptions(store).map(y => (
                <option key={y} value={y}>
                    {y}{y === current ? ' (actual)' : ''}
                </option>
            ))}
        </select>
    );
};

export default YearSelect;
