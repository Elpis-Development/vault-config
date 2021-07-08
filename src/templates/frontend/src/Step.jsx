const StepType = {
    active: "is-active",
    finished: "is-finished",
    failed: "is-failed",
    none: "is-none"
};

const getClassName = (state) => {
    switch (state) {
        case "active":
            return StepType.active;
        case "finished":
            return StepType.finished;
        case "failed":
            return StepType.failed;
        default:
            return StepType.none;
   }
};

const Step = (props) => {
    let className = props.type ? getClassName(props.type) : "";

    return (
         <li className={className}>
            <div></div>
            <span><strong>{props.title}</strong> {props.description}</span>
         </li>
    );
};